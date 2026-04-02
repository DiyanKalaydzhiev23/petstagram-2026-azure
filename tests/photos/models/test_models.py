from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from model_bakery import baker

from photos.models import Photo
from photos.validators import FileSizeValidator


class PhotoModelsTests(TestCase):
    def setUp(self):
        self.user = baker.make(
            get_user_model(),
            email="photo-example@gmail.com"
        )  # Creates the object and saves it in the db

    def test_photo_description_must_be_at_least_ten_characters(self):
        # Arrange
        photo = baker.prepare(
            Photo,
            photo="sample",
            description="short",
            user=self.user
        )  # Creates the object in memory

        # Act
        with self.assertRaises(ValidationError) as error:
            photo.full_clean()

        # Assert
        self.assertIn("description", error.exception.message_dict)

    def test_photo_sets_publication_date_automatically(self):
        photo = baker.make(
            Photo,
            photo="sample",
            user=self.user
        )

        self.assertIsNotNone(photo.date_of_publication)


class FileSizeValidatorTests(TestCase):
    def test_file_size_validator_raises_for_files_over_limit(self):
        # Arrange
        validator = FileSizeValidator(file_size=1)  # 1 MB
        file = SimpleUploadedFile("large.jpg", b"a" * (1024 * 1024 + 1), content_type="image/jpeg")

        # Act + Assert
        with self.assertRaises(ValidationError):
            validator(file)

    def test_file_size_validator_uses_custom_message(self):
        # Arrange
        validator = FileSizeValidator(file_size=1, message="Custom Message")  # 1 MB
        file = SimpleUploadedFile("large.jpg", b"a" * (1024 * 1024 + 1), content_type="image/jpeg")

        # Act + Assert
        with self.assertRaisesMessage(ValidationError, "Custom Message"):
            validator(file)
