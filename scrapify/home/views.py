from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from .forms import (
    BuyerRegistrationForm,
    LoginForm,
    SellerDashboardListingForm,
    SellerRegistrationForm,
    create_user_and_buyer_profile,
    create_user_and_seller_profile,
)
from .models import Bid, PickupOrder, ScrapCategory, ScrapListing


def _ensure_default_categories():
    if ScrapCategory.objects.exists():
        return

    default_categories = [
        "Paper",
        "Plastic",
        "Metal",
        "Glass",
        "E-waste",
    ]
    ScrapCategory.objects.bulk_create([ScrapCategory(name=name) for name in default_categories])


def _resolve_user_for_login(username_or_email):
    user_model = get_user_model()
    candidate = username_or_email.strip()
    if "@" in candidate:
        matched_user = user_model.objects.filter(email__iexact=candidate).first()
        if matched_user:
            return matched_user.get_username()
    return candidate


def _is_buyer(user):
    return user.is_authenticated and hasattr(user, "buyer_profile")


def _is_seller(user):
    return user.is_authenticated and hasattr(user, "seller_profile")


def buyer_required(view_func):
    @login_required(login_url="buyer_auth")
    def _wrapped(request, *args, **kwargs):
        if not _is_buyer(request.user):
            messages.error(request, "Buyer access required.")
            return redirect("buyer_auth")
        return view_func(request, *args, **kwargs)

    return _wrapped


def seller_required(view_func):
    @login_required(login_url="seller_auth")
    def _wrapped(request, *args, **kwargs):
        if not _is_seller(request.user):
            messages.error(request, "Seller access required.")
            return redirect("seller_auth")
        return view_func(request, *args, **kwargs)

    return _wrapped


def landing(request):
    return render(request, "landing.html")


def buyauth(request):
    login_form = LoginForm()
    register_form = BuyerRegistrationForm()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "login":
            login_form = LoginForm(request.POST)
            if login_form.is_valid():
                username_or_email = login_form.cleaned_data["username_or_email"]
                password = login_form.cleaned_data["password"]
                username = _resolve_user_for_login(username_or_email)
                user = authenticate(request, username=username, password=password)

                if user is None:
                    messages.error(request, "Invalid login credentials.")
                elif not hasattr(user, "buyer_profile"):
                    messages.error(request, "This account is not registered as a buyer.")
                else:
                    login(request, user)
                    messages.success(request, "Logged in successfully.")
                    return redirect("buyer_dashboard")
            else:
                for errors in login_form.errors.values():
                    for error in errors:
                        messages.error(request, error)

        elif action == "register":
            register_form = BuyerRegistrationForm(request.POST)
            if register_form.is_valid():
                with transaction.atomic():
                    create_user_and_buyer_profile(register_form.cleaned_data)
                messages.success(request, "Buyer account created. Please log in.")
                return redirect("buyer_auth")
            else:
                for errors in register_form.errors.values():
                    for error in errors:
                        messages.error(request, error)

        else:
            messages.error(request, "Invalid request.")

    context = {
        "login_form": login_form,
        "register_form": register_form,
    }
    return render(request, "buyer_auth.html", context)


def sellerauth(request):
    login_form = LoginForm()
    register_form = SellerRegistrationForm()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "login":
            login_form = LoginForm(request.POST)
            if login_form.is_valid():
                username_or_email = login_form.cleaned_data["username_or_email"]
                password = login_form.cleaned_data["password"]
                username = _resolve_user_for_login(username_or_email)
                user = authenticate(request, username=username, password=password)

                if user is None:
                    messages.error(request, "Invalid login credentials.")
                elif not hasattr(user, "seller_profile"):
                    messages.error(request, "This account is not registered as a seller.")
                else:
                    login(request, user)
                    messages.success(request, "Logged in successfully.")
                    return redirect("seller_dashboard")
            else:
                for errors in login_form.errors.values():
                    for error in errors:
                        messages.error(request, error)

        elif action == "register":
            register_form = SellerRegistrationForm(request.POST)
            if register_form.is_valid():
                with transaction.atomic():
                    create_user_and_seller_profile(register_form.cleaned_data)
                messages.success(request, "Seller account created. Please log in.")
                return redirect("seller_auth")
            else:
                for errors in register_form.errors.values():
                    for error in errors:
                        messages.error(request, error)

        else:
            messages.error(request, "Invalid request.")

    context = {
        "login_form": login_form,
        "register_form": register_form,
    }
    return render(request, "seller_auth.html", context)


@buyer_required
def buyerdashboard(request):
    buyer_profile = request.user.buyer_profile

    if request.method == "POST" and request.POST.get("action") == "book_listing":
        listing_id = request.POST.get("listing_id")
        scheduled_pickup_input = request.POST.get("scheduled_pickup_at", "").strip()

        if not scheduled_pickup_input:
            messages.error(request, "Please assign a pickup time before booking.")
            return redirect("buyer_dashboard")

        scheduled_pickup_at = parse_datetime(scheduled_pickup_input)
        if scheduled_pickup_at is None:
            messages.error(request, "Please provide a valid pickup time.")
            return redirect("buyer_dashboard")

        if timezone.is_naive(scheduled_pickup_at):
            scheduled_pickup_at = timezone.make_aware(
                scheduled_pickup_at,
                timezone.get_current_timezone(),
            )

        listing = get_object_or_404(
            ScrapListing.objects.select_related("seller", "category"),
            pk=listing_id,
            status=ScrapListing.Status.AVAILABLE,
        )

        existing_booking = PickupOrder.objects.filter(
            buyer=buyer_profile,
            listing=listing,
        ).exclude(status=PickupOrder.Status.CANCELLED).first()

        if existing_booking:
            messages.info(request, "You have already booked this listing.")
            return redirect("buyer_dashboard")

        with transaction.atomic():
            bid, _ = Bid.objects.select_for_update().get_or_create(
                listing=listing,
                buyer=buyer_profile,
                defaults={
                    "quantity_kg": listing.quantity_kg,
                    "bid_price_per_kg": listing.price_per_kg,
                    "message": "Booked directly from buyer dashboard.",
                    "status": Bid.Status.ACCEPTED,
                },
            )

            if bid.status != Bid.Status.ACCEPTED:
                bid.quantity_kg = listing.quantity_kg
                bid.bid_price_per_kg = listing.price_per_kg
                bid.status = Bid.Status.ACCEPTED
                bid.message = "Booked directly from buyer dashboard."
                bid.save(update_fields=["quantity_kg", "bid_price_per_kg", "status", "message", "updated_at"])

            PickupOrder.objects.update_or_create(
                bid=bid,
                defaults={
                    "listing": listing,
                    "buyer": buyer_profile,
                    "seller": listing.seller,
                    "scheduled_pickup_at": scheduled_pickup_at,
                    "pickup_address": listing.seller.pickup_address,
                    "status": PickupOrder.Status.CONFIRMED,
                    "total_amount": bid.total_value,
                },
            )

            listing.status = ScrapListing.Status.RESERVED
            listing.save(update_fields=["status", "updated_at"])

        messages.success(request, "Booking confirmed. Pickup has been scheduled.")
        return redirect("buyer_dashboard")

    available_listings = ScrapListing.objects.filter(
        status=ScrapListing.Status.AVAILABLE,
    ).select_related("seller", "category")

    my_bookings = PickupOrder.objects.filter(
        buyer=buyer_profile,
    ).exclude(status=PickupOrder.Status.CANCELLED).select_related("listing", "seller", "listing__category")

    context = {
        "available_listings": available_listings,
        "my_bookings": my_bookings,
    }
    return render(request, "buyer_dashboard.html", context)


@seller_required
def sellerdashboard(request):
    seller_profile = request.user.seller_profile
    _ensure_default_categories()

    if request.method == "POST" and request.POST.get("action") == "create_listing":
        listing_form = SellerDashboardListingForm(request.POST)
        if listing_form.is_valid():
            listing = listing_form.save(commit=False)
            listing.seller = seller_profile
            listing.status = ScrapListing.Status.AVAILABLE
            listing.save()
            messages.success(request, "Listing added successfully.")
            return redirect("seller_dashboard")
        for errors in listing_form.errors.values():
            for error in errors:
                messages.error(request, error)
    else:
        listing_form = SellerDashboardListingForm()

    listings = ScrapListing.objects.filter(seller=seller_profile).select_related("category")
    bookings = PickupOrder.objects.filter(
        seller=seller_profile,
    ).exclude(status=PickupOrder.Status.CANCELLED).select_related("listing", "buyer")

    context = {
        "total_listings_count": listings.count(),
        "available_listings_count": listings.filter(status=ScrapListing.Status.AVAILABLE).count(),
        "bookings_count": bookings.count(),
        "listings": listings,
        "bookings": bookings[:10],
        "listing_form": listing_form,
    }
    return render(request, "seller_dashboard.html", context)


def about(request):
    return render(request, "about.html")


@seller_required
def seller_listing_edit(request, listing_id):
    listing = get_object_or_404(ScrapListing, pk=listing_id, seller=request.user.seller_profile)

    if request.method == "POST":
        form = SellerDashboardListingForm(request.POST, instance=listing)
        if form.is_valid():
            form.save()
            messages.success(request, "Listing updated successfully.")
            return redirect("seller_dashboard")
    else:
        form = SellerDashboardListingForm(instance=listing)

    return render(request, "seller_listing_form.html", {"form": form, "mode": "edit", "listing": listing})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("landing")
