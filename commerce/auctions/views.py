from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User, Listing, Category, Comments, Bid


def listing(request, id):
    listingData = Listing.objects.get(pk=id)
    ListingInWatchlist = request.user in listingData.watchlist.all()
    allComments = Comments.objects.filter(listing=listingData)
    isOwner = request.user.username == listingData.owner.username
    return render(request, "auctions/listing.html", {
        'listing': listingData,
        'ListingInWatchlist': ListingInWatchlist,
        'allComments': allComments,
        'isOwner': isOwner
    })

def closeAuction(request, id):
    listingData = Listing.objects.get(pk=id)
    listingData.isActive = False
    listingData.save()
    isOwner = request.user.username == listingData.owner.username
    ListingInWatchlist = request.user in listingData.watchlist.all()
    allComments = Comments.objects.filter(listing=listingData)  
    return render(request, "auctions/listing.html", {
        'listing': listingData,
        'ListingInWatchlist': ListingInWatchlist,
        'allComments': allComments,
        'update': True,
        'isOwner': isOwner,
        'message': "Congratulations! Your auction is closed!"
    })

def displayWatchlist(request):
    currentUser = request.user
    listings = currentUser.listingWatchlist.all()
    return render(request, "auctions/watchlist.html", {
        "listings": listings
    })

def addBid(request, id):
    newBid = request.POST['newBid']
    listingData = Listing.objects.get(pk=id)
    ListingInWatchlist = request.user in listingData.watchlist.all()
    allComments = Comments.objects.filter(listing=listingData)
    isOwner = request.user.username == listingData.owner.username
    if int(newBid) > listingData.price.bid:
        updateBid = Bid(user=request.user, bid=int(newBid))
        updateBid.save()
        listingData.price = updateBid
        listingData.save()
        return render(request, "auctions/listing.html", {
            "listing": listingData,
            "message": "Bid was updated successfully",
            "update": True,
            'ListingInWatchlist': ListingInWatchlist,
            'allComments': allComments,
            'isOwner': isOwner
        })
    else:
        return render(request, "auctions/listing.html", {
            "listing": listingData,
            "message": "Need a higher bid!",
            "update": False,
            'ListingInWatchlist': ListingInWatchlist,
            'allComments': allComments,
            'isOwner': isOwner
        })

def addComment(request, id):
    currentUser = request.user
    listingData = Listing.objects.get(pk=id)
    message = request.POST['newComment']

    newComment = Comments(
        author = currentUser,
        listing = listingData,
        message = message
    )
    newComment.save()
    return HttpResponseRedirect(reverse('listing', args=(id, )))

def removeWatchlist(request, id):
    listingData = Listing.objects.get(pk=id)
    currentUser = request.user
    listingData.watchlist.remove(currentUser)
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def addWatchlist(request, id):
    listingData = Listing.objects.get(pk=id)
    currentUser = request.user
    listingData.watchlist.add(currentUser)
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def index(request):
    activeListings = Listing.objects.filter(isActive=True)
    allCategories = Category.objects.all()
    return render(request, "auctions/index.html", {
        'listings': activeListings,
        'categories': allCategories
    })

def displayCategory(request):
    if request.method == 'POST':
        categoryfromForm = request.POST['category']
        category = Category.objects.get(categoryName=categoryfromForm)
        activeListings = Listing.objects.filter(isActive=True, category=category)
        allCategories = Category.objects.all()
        return render(request, "auctions/index.html", {
            'listings': activeListings,
            'categories': allCategories
        })

def create_listing(request):
    if request.method == 'GET':
        allCategories = Category.objects.all()
        return render(request, "auctions/create.html", {
            "categories": allCategories
        })
    else:
        #Get the data from the form
        title = request.POST["title"]
        description = request.POST['description']
        imageUrl = request.POST['imageUrl']
        price = request.POST['price']
        category= request.POST['category']
        #who is the user?
        currentUser = request.user
        #Get all content about the particular category
        categoryData = Category.objects.get(categoryName=category)
        #creating a bid object
        bid = Bid(bid=int(price), user = currentUser)
        bid.save()
        #create a new listing object
        newListing = Listing(title=title, description=description, imageUrl=imageUrl, price=bid, category=categoryData, owner=currentUser)
        #then insert the object into our database
        newListing.save()
        #then redirect to the index page
        return HttpResponseRedirect(reverse(index))


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

