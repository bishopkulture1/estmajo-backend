"""Regression checks for the existing media and notification integrations."""
from unittest.mock import patch, MagicMock
from django.test import SimpleTestCase, override_settings
from core.media import delivery_url

@override_settings(IMAGEKIT_PRIVATE_KEY='test-private-not-real', IMAGEKIT_URL_ENDPOINT='https://ik.imagekit.io/test')
class SignedMediaTests(SimpleTestCase):
    @patch('core.media._signing_client')
    def test_video_playback_uses_signed_url(self, client):
        client.return_value.helper.build_url.return_value = 'https://ik.imagekit.io/test/video.mp4?ik-s=test'
        asset=MagicMock(kind='video', url='https://ik.imagekit.io/test/video.mp4')
        self.assertIn('ik-s=', delivery_url(asset))
        opts=client.return_value.helper.build_url.call_args.kwargs
        self.assertTrue(opts['signed'])
        self.assertEqual(opts['expires_in'], 3600)

    @patch('core.media._signing_client')
    def test_image_delivery_remains_private(self, client):
        client.return_value.helper.build_url.return_value = 'https://ik.imagekit.io/test/image.jpg?ik-s=test'
        asset=MagicMock(kind='image', url='https://ik.imagekit.io/test/image.jpg')
        delivery_url(asset, 960)
        opts=client.return_value.helper.build_url.call_args.kwargs
        self.assertTrue(opts['signed'])
        self.assertEqual(opts['transformation'][0]['width'], 960)
