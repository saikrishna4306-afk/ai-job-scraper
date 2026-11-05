from modules.applications.answer_manager import classify_question, normalize_question
from modules.applications.form_detector import FormDetector
from modules.applications.field_mapper import FieldMapper
from modules.intelligence.schemas import Profile


def test_sensitive_answers_are_not_auto_resolved():
    assert classify_question("Will you need visa sponsorship?") == "sensitive"
    assert normalize_question("Hello, World?") == "hello world"


def test_form_detection_and_profile_mapping():
    fields = FormDetector().detect_html('<label for="email">Email</label><input id="email" required><input name="phone">')
    values = FieldMapper().map(fields, Profile(email="a@example.com", phone="123"))
    assert values == {"email": "a@example.com", "phone": "123"}
