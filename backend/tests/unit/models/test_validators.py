"""Unit tests for model validators."""

from __future__ import annotations

import pytest

from app.models.billing import (
    Installment,
    Invoice,
    InvoiceItem,
    SiblingDiscountPolicy,
)
from app.models.documents import ResourceRating
from app.models.erp import Enrollment, EnrollmentStatus
from app.models.iam import User
from app.models.lms import Assignment, Grade, GradeCategory
from app.models.reporting import ReportJob, ReportJobStatus
from app.models.school import School


class TestUserValidators:
    def test_email_lowercased(self):
        user = User()

        assert user.validate_email("email", "JoHn@Test.COM") == "john@test.com"

    def test_email_stripped(self):
        user = User()

        assert user.validate_email("email", " a@b.c ") == "a@b.c"

    @pytest.mark.parametrize("value", ["notanemail", ""])
    def test_email_invalid(self, value: str):
        user = User()

        with pytest.raises(ValueError, match="Invalid email format"):
            user.validate_email("email", value)

    def test_phone_normalized(self):
        user = User()

        assert user.validate_phone("phone", "+212 6-12-34-56-78") == "+212612345678"

    def test_phone_none_is_allowed(self):
        user = User()

        assert user.validate_phone("phone", None) is None

    def test_phone_no_country_code(self):
        user = User()

        with pytest.raises(ValueError, match="Phone must start with country code"):
            user.validate_phone("phone", "0612345678")


class TestSchoolValidators:
    def test_email_normalized(self):
        school = School()

        assert (
            school.validate_email("email", " CONTACT@ECOLE.MA ") == "contact@ecole.ma"
        )

    def test_email_invalid(self):
        school = School()

        with pytest.raises(ValueError, match="Invalid school email"):
            school.validate_email("email", "invalid-school-email")


class TestGradeCategoryValidators:
    def test_weight_accepts_fractional_range(self):
        category = GradeCategory()

        assert category.validate_weight("weight", 0.5) == 0.5

    @pytest.mark.parametrize("value", [0, -0.1, 1.01])
    def test_weight_rejects_out_of_range_values(self, value: float):
        category = GradeCategory()

        with pytest.raises(
            ValueError, match="GradeCategory weight must be between 0 and 1"
        ):
            category.validate_weight("weight", value)


class TestAssignmentValidators:
    def test_total_points_positive(self):
        assignment = Assignment()

        assert assignment.validate_total_points("total_points", 20) == 20

    @pytest.mark.parametrize("value", [0, -1])
    def test_total_points_must_be_greater_than_zero(self, value: int):
        assignment = Assignment()

        with pytest.raises(
            ValueError,
            match="Assignment total_points must be greater than 0",
        ):
            assignment.validate_total_points("total_points", value)

    @pytest.mark.parametrize("value", [0.0, 2.5, 100.0])
    def test_late_penalty_per_day_accepts_range(self, value: float):
        assignment = Assignment()

        assert (
            assignment.validate_late_penalty_per_day("late_penalty_per_day", value)
            == value
        )

    @pytest.mark.parametrize("value", [-1.0, 100.1])
    def test_late_penalty_per_day_rejects_out_of_range(self, value: float):
        assignment = Assignment()

        with pytest.raises(
            ValueError,
            match="Assignment late_penalty_per_day must be between 0 and 100",
        ):
            assignment.validate_late_penalty_per_day("late_penalty_per_day", value)


class TestGradeValidators:
    @pytest.mark.parametrize("value", [0, 12.5, 20])
    def test_score_accepts_zero_to_twenty(self, value: float):
        grade = Grade()

        assert grade.validate_score("score", value) == value

    @pytest.mark.parametrize("value", [-1, 21])
    def test_score_rejects_values_outside_scale(self, value: float):
        grade = Grade()

        with pytest.raises(ValueError, match="Grade score must be between 0 and 20"):
            grade.validate_score("score", value)

    def test_late_penalty_accepts_zero(self):
        grade = Grade()

        assert grade.validate_late_penalty("late_penalty", 0) == 0

    def test_late_penalty_rejects_negative(self):
        grade = Grade()

        with pytest.raises(ValueError, match="Grade late_penalty must be non-negative"):
            grade.validate_late_penalty("late_penalty", -1)


class TestEnrollmentValidator:
    def test_status_accepts_enum_values(self):
        enrollment = Enrollment()

        assert (
            enrollment.validate_status("status", EnrollmentStatus.ACTIVE.value)
            == EnrollmentStatus.ACTIVE.value
        )

    def test_status_rejects_unknown_value(self):
        enrollment = Enrollment()

        with pytest.raises(ValueError, match="Enrollment status must be one of"):
            enrollment.validate_status("status", "paused")


class TestInvoiceValidators:
    def test_total_amount_accepts_zero(self):
        invoice = Invoice()

        assert invoice.validate_total_amount("total_amount", 0) == 0

    def test_total_amount_rejects_negative(self):
        invoice = Invoice()

        with pytest.raises(
            ValueError, match="Invoice total_amount must be non-negative"
        ):
            invoice.validate_total_amount("total_amount", -1)

    def test_currency_normalizes_to_uppercase(self):
        invoice = Invoice()

        assert invoice.validate_currency("currency", " mad ") == "MAD"

    def test_currency_rejects_unknown_codes(self):
        invoice = Invoice()

        with pytest.raises(ValueError, match="Invoice currency must be one of"):
            invoice.validate_currency("currency", "XYZ")


class TestInvoiceItemValidator:
    def test_amount_accepts_zero(self):
        item = InvoiceItem()

        assert item.validate_amount("amount", 0) == 0

    def test_amount_rejects_negative(self):
        item = InvoiceItem()

        with pytest.raises(ValueError, match="InvoiceItem amount must be non-negative"):
            item.validate_amount("amount", -0.01)


class TestSiblingDiscountPolicyValidator:
    @pytest.mark.parametrize("value", [0, 25, 100])
    def test_discount_percent_accepts_zero_to_hundred(self, value: float):
        policy = SiblingDiscountPolicy()

        assert policy.validate_discount_percent("second_child_percent", value) == value

    @pytest.mark.parametrize("value", [-1, 101])
    def test_discount_percent_rejects_values_outside_range(self, value: float):
        policy = SiblingDiscountPolicy()

        with pytest.raises(
            ValueError, match="second_child_percent must be between 0 and 100"
        ):
            policy.validate_discount_percent("second_child_percent", value)


class TestInstallmentValidator:
    def test_amount_accepts_positive_values(self):
        installment = Installment()

        assert installment.validate_amount("amount", 500.0) == 500.0

    @pytest.mark.parametrize("value", [0, -1])
    def test_amount_rejects_zero_and_negative(self, value: float):
        installment = Installment()

        with pytest.raises(
            ValueError, match="Installment amount must be greater than 0"
        ):
            installment.validate_amount("amount", value)


class TestResourceRatingValidator:
    @pytest.mark.parametrize("value", [1, 3, 5])
    def test_rating_accepts_one_to_five(self, value: int):
        rating = ResourceRating()

        assert rating.validate_rating("rating", value) == value

    @pytest.mark.parametrize("value", [0, 6])
    def test_rating_rejects_out_of_range_values(self, value: int):
        rating = ResourceRating()

        with pytest.raises(
            ValueError, match="ResourceRating rating must be between 1 and 5"
        ):
            rating.validate_rating("rating", value)


class TestReportJobValidator:
    def test_status_accepts_known_value(self):
        job = ReportJob()

        assert (
            job.validate_status("status", ReportJobStatus.READY.value)
            == ReportJobStatus.READY.value
        )

    def test_status_rejects_unknown_value(self):
        job = ReportJob()

        with pytest.raises(ValueError, match="ReportJob status must be one of"):
            job.validate_status("status", "queued")
