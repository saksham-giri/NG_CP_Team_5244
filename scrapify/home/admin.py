from django.contrib import admin
from .models import (
	Bid,
	BuyerProfile,
	PickupOrder,
	ScrapCategory,
	ScrapListing,
	SellerProfile,
)


@admin.register(BuyerProfile)
class BuyerProfileAdmin(admin.ModelAdmin):
	list_display = ("business_name", "user", "created_at")
	list_filter = ("created_at",)
	search_fields = ("business_name", "user__username", "user__email")


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
	list_display = ("business_name", "user", "pickup_address", "created_at")
	list_filter = ("created_at",)
	search_fields = ("business_name", "user__username", "user__email")


@admin.register(ScrapCategory)
class ScrapCategoryAdmin(admin.ModelAdmin):
	list_display = ("name", "created_at")
	search_fields = ("name",)


@admin.register(ScrapListing)
class ScrapListingAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"seller",
		"category",
		"description",
		"quantity_kg",
		"price_per_kg",
		"location",
		"status",
		"created_at",
	)
	list_filter = ("status", "category", "created_at")
	search_fields = ("seller__business_name", "category__name", "description", "location")


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
	list_display = (
		"listing",
		"buyer",
		"quantity_kg",
		"bid_price_per_kg",
		"status",
		"created_at",
	)
	list_filter = ("status", "created_at")
	search_fields = ("listing__category__name", "buyer__business_name")


@admin.register(PickupOrder)
class PickupOrderAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"listing",
		"buyer",
		"seller",
		"status",
		"total_amount",
		"scheduled_pickup_at",
	)
	list_filter = ("status", "created_at")
	search_fields = (
		"listing__category__name",
		"buyer__business_name",
		"seller__business_name",
	)
