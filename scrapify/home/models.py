from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class TimeStampedModel(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True


class BuyerProfile(TimeStampedModel):
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="buyer_profile",
	)
	business_name = models.CharField(max_length=255)
	phone_number = models.CharField(max_length=20)
	address = models.TextField(blank=True)

	def __str__(self):
		return self.business_name


class SellerProfile(TimeStampedModel):
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="seller_profile",
	)
	business_name = models.CharField(max_length=255)
	phone_number = models.CharField(max_length=20, blank=True)
	pickup_address = models.TextField()

	def __str__(self):
		return self.business_name


class ScrapCategory(TimeStampedModel):
	name = models.CharField(max_length=120, unique=True)
	description = models.TextField(blank=True)

	class Meta:
		verbose_name_plural = "Scrap categories"
		ordering = ["name"]

	def __str__(self):
		return self.name


class ScrapListing(TimeStampedModel):
	class Status(models.TextChoices):
		AVAILABLE = "available", "Available"
		RESERVED = "reserved", "Reserved"
		SOLD = "sold", "Sold"
		INACTIVE = "inactive", "Inactive"

	seller = models.ForeignKey(
		SellerProfile,
		on_delete=models.CASCADE,
		related_name="listings",
	)
	category = models.ForeignKey(
		ScrapCategory,
		on_delete=models.PROTECT,
		related_name="listings",
	)
	description = models.TextField()
	quantity_kg = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		validators=[MinValueValidator(Decimal("0.01"))],
	)
	price_per_kg = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		validators=[MinValueValidator(Decimal("0.01"))],
	)
	location = models.CharField(max_length=255)
	status = models.CharField(
		max_length=15,
		choices=Status.choices,
		default=Status.AVAILABLE,
	)

	class Meta:
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["status"]),
			models.Index(fields=["category", "status"]),
		]
		constraints = [
			models.CheckConstraint(
				condition=models.Q(quantity_kg__gt=Decimal("0.00")),
				name="listing_quantity_gt_0",
				
			),
			models.CheckConstraint(
				condition=models.Q(price_per_kg__gt=Decimal("0.00")),
				name="listing_price_gt_0",
			),
		]

	def __str__(self):
		return f"{self.category.name} - {self.seller.business_name}"


class Bid(TimeStampedModel):
	class Status(models.TextChoices):
		PENDING = "pending", "Pending"
		ACCEPTED = "accepted", "Accepted"
		REJECTED = "rejected", "Rejected"
		WITHDRAWN = "withdrawn", "Withdrawn"

	listing = models.ForeignKey(
		ScrapListing,
		on_delete=models.CASCADE,
		related_name="bids",
	)
	buyer = models.ForeignKey(
		BuyerProfile,
		on_delete=models.CASCADE,
		related_name="bids",
	)
	quantity_kg = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		validators=[MinValueValidator(Decimal("0.01"))],
	)
	bid_price_per_kg = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		validators=[MinValueValidator(Decimal("0.01"))],
	)
	message = models.TextField(blank=True)
	status = models.CharField(
		max_length=15,
		choices=Status.choices,
		default=Status.PENDING,
	)

	class Meta:
		ordering = ["-created_at"]
		constraints = [
			models.UniqueConstraint(
				fields=["listing", "buyer"],
				name="unique_bid_per_buyer_per_listing",
			),
			models.CheckConstraint(
				condition=models.Q(quantity_kg__gt=Decimal("0.00")),
				name="bid_quantity_gt_0",
			),
			models.CheckConstraint(
				condition=models.Q(bid_price_per_kg__gt=Decimal("0.00")),
				name="bid_price_gt_0",
			),
		]

	@property
	def total_value(self):
		return self.quantity_kg * self.bid_price_per_kg

	def __str__(self):
		return f"Bid by {self.buyer.business_name} on {self.listing.category.name}"


class PickupOrder(TimeStampedModel):
	class Status(models.TextChoices):
		PLACED = "placed", "Placed"
		CONFIRMED = "confirmed", "Confirmed"
		PICKED_UP = "picked_up", "Picked Up"
		COMPLETED = "completed", "Completed"
		CANCELLED = "cancelled", "Cancelled"

	listing = models.ForeignKey(
		ScrapListing,
		on_delete=models.PROTECT,
		related_name="orders",
	)
	bid = models.OneToOneField(
		Bid,
		on_delete=models.PROTECT,
		related_name="order",
	)
	buyer = models.ForeignKey(
		BuyerProfile,
		on_delete=models.PROTECT,
		related_name="orders",
	)
	seller = models.ForeignKey(
		SellerProfile,
		on_delete=models.PROTECT,
		related_name="orders",
	)
	scheduled_pickup_at = models.DateTimeField(null=True, blank=True)
	pickup_address = models.TextField(blank=True)
	status = models.CharField(
		max_length=15,
		choices=Status.choices,
		default=Status.PLACED,
	)
	total_amount = models.DecimalField(
		max_digits=12,
		decimal_places=2,
		validators=[MinValueValidator(Decimal("0.01"))],
	)

	class Meta:
		ordering = ["-created_at"]
		indexes = [
			models.Index(fields=["status"]),
			models.Index(fields=["buyer", "status"]),
			models.Index(fields=["seller", "status"]),
		]
		constraints = [
			models.CheckConstraint(
				condition=models.Q(total_amount__gt=Decimal("0.00")),
				name="order_total_gt_0",
			)
		]

	def __str__(self):
		return f"Order #{self.pk} - {self.listing.category.name}"
