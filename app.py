from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
from sqlalchemy import select

from config import Settings
from database.database import session_scope
from database.models import Application, Job, OutreachEmail
from database.repositories import summary
from modules.intelligence.resume_engine import extract_resume_text, propose_profile_from_resume

settings = Settings.load()
st.set_page_config(page_title="Autonomous Job Hunter", layout="wide")
st.title("Autonomous AI Job Hunter")
st.caption("Approval-first job discovery, document preparation, applications and outreach")

with st.sidebar:
    page = st.radio("Navigate", ["Home", "Jobs", "Applications", "Resumes & Profile", "Outreach", "Interview Prep", "Settings"])

with session_scope(settings) as session:
    if page == "Home":
        st.subheader("Overview")
        stats = summary(session)
        cols = st.columns(len(stats))
        for col, (label, value) in zip(cols, stats.items()):
            col.metric(label.replace("_", " ").title(), value)
        st.subheader("Recent jobs")
        for job in session.scalars(select(Job).order_by(Job.discovered_at.desc()).limit(10)):
            st.write(f"**{job.title}** — {job.company} · {job.location or 'Location not specified'} · [{job.source_name}]({job.application_url})")
    elif page == "Jobs":
        st.subheader("Discovered jobs")
        minimum = st.slider("Minimum match score", 1, 10, settings.minimum_match_score)
        for job in session.scalars(select(Job).order_by(Job.discovered_at.desc())):
            match = job.job_matches[0] if job.job_matches else None
            if match and match.match_score < minimum:
                continue
            st.markdown(f"### {job.title} — {job.company}")
            st.write(f"{job.location or 'Unknown location'} · {job.remote_eligibility or 'Unknown remote eligibility'} · Score: {match.match_score if match else 'Pending'} · {job.source_name}")
            st.link_button("Open application", job.application_url)
            with st.expander("Description"):
                st.write(job.description[:4000])
    elif page == "Applications":
        st.subheader("Applications")
        for item in session.scalars(select(Application).order_by(Application.id.desc())):
            st.write(f"**{item.job.company} — {item.job.title}** · `{item.status}` · approval: `{item.approval_status}`")
            if item.error_info:
                st.error(item.error_info)
            if item.status == "PENDING_APPROVAL" and st.button("Approve assisted application", key=f"approve_{item.id}"):
                item.approval_status = "APPROVED"
                item.status = "READY_TO_SUBMIT"
                st.success("Approved for the supported application flow; final submission still requires portal evidence.")
    elif page == "Outreach":
        st.subheader("Outreach drafts")
        st.info("Draft-only by default. Contacts must be explicitly supplied from public sources; no email is fabricated.")
        for item in session.scalars(select(OutreachEmail).order_by(OutreachEmail.id.desc())):
            with st.expander(f"{item.contact_role}: {item.company} — {item.recipient_name or item.recipient_email or 'unaddressed'}"):
                st.write(f"Verification: `{item.verification_status}` · Status: `{item.sending_status}`")
                st.text_input("Subject", item.subject, key=f"subject_{item.id}")
                st.text_area("Body", item.body, height=220, key=f"body_{item.id}")
    elif page == "Resumes & Profile":
        st.subheader("Profile onboarding")
        profile_path = Path("master_profile.json")
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        uploaded = st.file_uploader("Upload original PDF or DOCX resume", type=["pdf", "docx"])
        if uploaded and st.button("Extract proposal"):
            target = Path("storage/resumes") / uploaded.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(uploaded.getvalue())
            proposal = propose_profile_from_resume(extract_resume_text(target))
            st.json(proposal)
            st.warning("Review this proposal and edit the profile before marking it verified.")
        verified = st.checkbox("Profile verified", value=bool(profile.get("verified")))
        name = st.text_input("Full name", profile.get("full_name", ""))
        email = st.text_input("Email", profile.get("email", ""))
        location = st.text_input("Location", profile.get("location", ""))
        if st.button("Save verified profile"):
            profile.update({"verified": verified, "full_name": name, "email": email, "location": location})
            profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
            st.success("Profile saved")
    elif page == "Interview Prep":
        st.subheader("Interview preparation")
        for path in sorted(Path("storage/interview_prep").glob("*/interview_preparation.md")):
            st.markdown(f"**{path.parent.name}**")
            st.download_button("Download preparation", path.read_bytes(), file_name=path.name, key=str(path))
    else:
        st.subheader("Configuration status")
        for key, value in settings.status().items():
            st.write(f"**{key}:** {value}")
        st.json({"timezone": settings.timezone, "lookback_hours": settings.job_lookback_hours, "minimum_match_score": settings.minimum_match_score, "auto_apply": settings.auto_apply_enabled, "require_approval": settings.require_approval})
        st.subheader("Add a permitted custom source")
        source_name = st.text_input("Source name")
        source_url = st.text_input("RSS or JSON URL")
        source_method = st.selectbox("Method", ["rss", "json"])
        rss_url = st.text_input("RSS URL (when method is RSS)")
        if st.button("Save custom source"):
            custom_path = Path("custom_sources.json")
            sources = json.loads(custom_path.read_text(encoding="utf-8")) if custom_path.exists() else []
            sources.append({"name": source_name, "url": source_url, "method": source_method, "rss_url": rss_url or None, "enabled": True})
            custom_path.write_text(json.dumps(sources, indent=2), encoding="utf-8")
            st.success("Custom source saved")
