from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Bid, BuyerProfile, PickupOrder, ScrapCategory, ScrapListing, SellerProfile


class SimplifiedFlowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()

        self.buyer_user = user_model.objects.create_user(
            username="buyer1",
            email="buyer@example.com",
            password="buyerpass123",
        )
        self.buyer_profile = BuyerProfile.objects.create(
            user=self.buyer_user,
            business_name="Buyer Biz",
            phone_number="1234567890",
        )

        self.seller_user = user_model.objects.create_user(
            username="seller1",
            email="seller@example.com",
            password="sellerpass123",
        )
        self.seller_profile = SellerProfile.objects.create(
            user=self.seller_user,
            business_name="Seller Biz",
            phone_number="9876543210",
            pickup_address="Warehouse 42",
        )

        self.category = ScrapCategory.objects.create(name="Metal")
        self.listing = ScrapListing.objects.create(
            seller=self.seller_profile,
            category=self.category,
            description="Mixed steel parts",
            quantity_kg=Decimal("100.00"),
            price_per_kg=Decimal("50.00"),
            location="Area 17",
        )

    def test_buyer_dashboard_requires_authentication(self):
        response = self.client.get(reverse("buyer_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("buyer_auth"), response.url)

    def test_buyer_can_book_listing_from_dashboard(self):
        self.client.force_login(self.buyer_user)
        response = self.client.post(
            reverse("buyer_dashboard"),
            {
                "action": "book_listing",
                "listing_id": self.listing.id,
                "scheduled_pickup_at": "2026-02-20T10:30",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        bid = Bid.objects.get(listing=self.listing, buyer=self.buyer_profile)
        order = PickupOrder.objects.get(bid=bid)
        self.listing.refresh_from_db()

        self.assertEqual(bid.status, Bid.Status.ACCEPTED)
        self.assertEqual(self.listing.status, ScrapListing.Status.RESERVED)
        self.assertEqual(order.status, PickupOrder.Status.CONFIRMED)
        self.assertEqual(order.total_amount, Decimal("5000.00"))

    def test_seller_dashboard_shows_own_listing(self):
        self.client.force_login(self.seller_user)
        response = self.client.get(reverse("seller_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Metal Listing")

    def test_seller_can_create_listing_from_dashboard(self):
        self.client.force_login(self.seller_user)
        response = self.client.post(
            reverse("seller_dashboard"),
            {
                "action": "create_listing",
                "category": self.category.id,
                "description": "PET bottles",
                "quantity_kg": "20.00",
                "price_per_kg": "12.50",
                "location": "Block A",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            ScrapListing.objects.filter(
                seller=self.seller_profile,
                description="PET bottles",
                quantity_kg=Decimal("20.00"),
                price_per_kg=Decimal("12.50"),
                location="Block A",
            ).exists()
        )
