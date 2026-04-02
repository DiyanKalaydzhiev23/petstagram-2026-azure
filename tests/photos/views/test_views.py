from unittest.mock import patch
from cloudinary import CloudinaryResource
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from common.models import Like
from pets.models import Pet
from photos.models import Photo


class PhotoViewsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = baker.make(user_model)
        self.other_user = baker.make(user_model)
        self.pet = baker.make(Pet, user=self.owner)
        self.photo = baker.make(
            Photo,
            user=self.owner,
            photo="sample",
        )
        self.photo.tagged_pets.add(self.pet)

    def build_cloudinary_resource(self, public_id):
        return CloudinaryResource(
            public_id=public_id,
            format="jpg",
            version=1,
            type="upload",
            resource_type="image",
        )

    def make_uploaded_image(self, name="photo.jpg"):
        return SimpleUploadedFile(
            name=name,
            content=b"fake-data-here",
            content_type='image/jpeg',
        )

    def test_photo_add_requires_login(self):
        response = self.client.get(reverse('photos:add'))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('photos:add')}",
            fetch_redirect_response=False,
        )

    def test_photo_add_uses_expected_template_for_authenticated_user(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('photos:add'))

        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'photos/photo-add-page.html')

    @patch("cloudinary.uploader.upload_resource")
    def test_photo_add_creates_photo_with_valid_data_redirects_to_home_page(self, mocked_upload):
        mocked_upload.return_value = self.build_cloudinary_resource("added-photo")
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse('photos:add'),
            data={
                "description": "Some really really really really long text here!!!!!",
                "location": "Sofia",
                "tagged_pets": [self.pet.pk],
                "photo": self.make_uploaded_image(),
            }
        )

        created_photo = Photo.objects.exclude(pk=self.photo.pk).get()

        self.assertRedirects(response, reverse('common:home'))
        self.assertEqual(self.owner, created_photo.user)
        self.assertEqual("Sofia", created_photo.location)

    def test_photo_details_uses_expected_template(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('photos:details'))

        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'photos/photo-details-page.html')

    def test_photo_details_marks_photo_as_liked_by_authenticated_user(self):
        baker.make(Like, to_photo=self.photo, user=self.other_user)
        self.client.force_login(self.other_user)

        response = self.client.get(reverse('photos:details', kwargs={'pk': self.photo.pk}))

        self.assertTrue(response.context['photo'].is_liked_by_user)

    def test_photo_details_does_not_mark_photo_as_liked_by_not_authenticated_user(self):
        baker.make(Like, to_photo=self.photo, user=self.other_user)

        response = self.client.get(reverse('photos:details', kwargs={'pk': self.photo.pk}))

        self.assertFalse(response.context['photo'].is_liked_by_user)

    def test_photo_edit_requires_login(self):
        response = self.client.get(reverse('photos:edit', kwargs={'pk': self.photo.pk}))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('photos:edit', kwargs={'pk': self.photo.pk})}",
            fetch_redirect_response=False,
        )


    def test_photo_edit_uses_expected_template_for_authenticated_user(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('photos:edit', kwargs={'pk': self.photo.pk}))

        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'photos/photo-edit-page.html')

    @patch("cloudinary.uploader.upload_resource")
    def test_photo_edit_updates_photo_with_valid_data_redirects_to_photo_details_page(self, mocked_upload):
        mocked_upload.return_value = self.build_cloudinary_resource("updated-photo")
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse('photos:edit', kwargs={'pk': self.photo.pk}),
            data={
                "description": "Some really really really really long text here!!!!!",
                "location": "Sofia",
                "tagged_pets": [self.pet.pk],
                "photo": self.make_uploaded_image(),
            }
        )

        self.photo.refresh_from_db()

        self.assertRedirects(response, reverse('photos:details', kwargs={'pk': self.photo.pk}))
        self.assertEqual(self.owner, self.photo.user)
        self.assertEqual("Some really really really really long text here!!!!!", self.photo.description)

    def test_photo_edit_blocks_non_author_user(self):
        self.client.force_login(self.other_user)

        response = self.client.get(reverse('photos:edit', kwargs={'pk': self.photo.pk}))

        self.assertEqual(403, response.status_code)

    def test_photo_delete_blocks_non_author_user(self):
        self.client.force_login(self.other_user)

        response = self.client.get(reverse('photos:edit', kwargs={'pk': self.photo.pk}))

        self.assertEqual(403, response.status_code)