from django.contrib.auth import get_user_model
from django.test import TestCase
from model_bakery import baker
from pets.models import Pet
from photos.forms import PhotoForm


class PhotoFormTests(TestCase):
    def setUp(self):
        self.user = baker.make(get_user_model())
        self.pet = baker.make(Pet, user=self.user)

    def test_photo_form_excludes_user_field(self):
        form = PhotoForm()

        self.assertNotIn('user', form.fields)
        self.assertEqual(
            ["description", "location", "photo", "tagged_pets"],
            sorted(form.fields.keys())
        )

    def test_photo_form_validates_description_length(self):
        form = PhotoForm(
            data={
                "description": "short",
                "location": "Sofia",
                "tagged_pets": [self.pet],
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("description", form.errors)