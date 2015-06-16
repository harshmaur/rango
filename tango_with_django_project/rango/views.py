from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from rango.models import Category, Page
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm
from django.contrib.auth.decorators import login_required
from datetime import datetime
from rango.bing_search import run_query
# Create your views here.

@login_required
def restricted(request):
	return HttpResponse("You can see this text because you are registered")

def index(request):
	category_list = Category.objects.order_by('-likes')[:5]
	context_dict = {'categories': category_list}

	pages_list = Page.objects.order_by('-views')[:5]
	context_dict['pages'] = pages_list



	visits = request.session.get('visits')
	if not visits:
		visits = 1


	## Get number of visits from Cookies, if DNE, then default to 1
	## Using int as cookies are stored as stringss
	# visits = int(request.COOKIES.get('visits', '1'))

	reset_last_visit_time = False

	last_visit = request.session.get('last_visit')
	if last_visit:
		last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")


	# does last_visit cookie exist?
	# if 'last_visit' in request.COOKIES:
	# 	last_visit = request.COOKIES['last_visit']

	# 	last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")

		# Last visit more than a day?
		if (datetime.now() - last_visit_time).days > 0:
			visits += 1

			# Last visit time to be updated now
			reset_last_visit_time = True

	else:
		# last_visit does not exist 
		reset_last_visit_time =True

		# Obtain response object for adding cookie info later.
		# response = render(request,'rango/index.html', context_dict)

	if reset_last_visit_time:
		request.session['last_visit'] = str(datetime.now())
		request.session['visits'] = visits 
	context_dict['visits'] = visits

	response = render(request, 'rango/index.html', context_dict)

	return response	
	# return HttpResponse("Rango says Hi   <br/> <a href='/rango/about'>About</a> ")

def about(request):
	# To be able to use the template rendering engine (if user_auth etc), use render(request, template, context_dict)
	return HttpResponse("Rango says here is the about page. <a href='/rango/''>Index</a>")

def category(request, category_name_slug):
	#create context dict for passing values to the template.
	context_dict = {}

	#Check if the category associated with the slug is already present in the database
	# if not then exception is raised. 
	try:
		category = Category.objects.get(slug= category_name_slug)
		context_dict['category_name'] = category.name
		
		#Retrieve all the associated pages.
		pages = Page.objects.filter(category=category).order_by('-views')

		#adds results to the context dict
		context_dict['pages'] = pages

		#passing category object to check if the category exists, in the template
		context_dict['category'] = category

		# passing category name slug for adding pages to category on the basis of slug.
		context_dict['category_name_slug'] = category_name_slug

	except Category.DoesNotExist:
		#Dont do anything, template displays the message for us. 
		pass

	if request.method =='POST':
		result_list=[]
		query = request.POST['query'].strip()

		if query:
			result_list=run_query(query)
		context_dict['result_list'] = result_list


	return render(request, 'rango/category.html', context_dict)

@login_required
def add_category(request):
	# A HTTP POST?
	if request.method == 'POST':
		form = CategoryForm(request.POST)

		# Have we been provided with a valid form?
		if form.is_valid():
			# Save the new category to the database.
			form.save(commit=True)

			# Now call the index() view.
			# The user will be shown the homepage.
			return index(request)
		else:
			# The supplied form contained errors - just print them to the terminal.
			print form.errors
	else:
		# If the request was not a POST, display the form to enter details.
		form = CategoryForm()

	# Bad form (or form details), no form supplied...
	# Render the form with error messages (if any).
	return render(request, 'rango/add_category.html', {'form': form})

@login_required
def add_page(request, category_name_slug):
	try:
		cat = Category.objects.get(slug  = category_name_slug)
	except Category.DoesNotExist:
		cat = None

	if request.method == 'POST':
		form = PageForm(request.POST)

		if form.is_valid():
			if cat:
				page = form.save(commit=False)
				page.category = cat
				page.views = 0
				page.save()

				return category(request, category_name_slug)
		else:
			print form.errors
	else:
		form = PageForm()

	context_dict = {'form' : form, 'category':category_name_slug}

	return render(request, 'rango/add_page.html', context_dict)

def register(request):
	
	# Boolean to tell the user has registered, setting it to false first
	registered = False

	if request.method == 'POST':
		user_form = UserForm(data = request.POST)
		profile_form = UserProfileForm(data = request.POST)

		if user_form.is_valid() and profile_form.is_valid():
			# Save the user's form data to the database.
			user = user_form.save()

			# password hashing
			user.set_password(user.password)
			user.save()


			# Now sort out the UserProfile instance.
			# Since we need to set the 'user' attribute ourselves, we set commit=False.
			# This delays saving the model until we're ready to avoid integrity problems.
			profile = profile_form.save(commit=False)
			profile.user = user

			# Fetching profile picture if user uploads

			if 'picture' in request.FILES:
				profile.picture = request.FILES['picture']

			profile.save()

			registered = True



		else:
			# Form not Valid
			print user_form.errors, profile_form.errors
	else:
		# Not a POST request
		user_form = UserForm()
		profile_form = UserProfileForm()


	# Render Template
	context_dict = {'user_form': user_form, 'profile_form': profile_form, 'registered':registered}
	return render(request, 'rango/register.html', context_dict)

def user_login(request):

	if request.method == 'POST':
		# Gather the username and password provided by the user.
		# This information is obtained from the login form.
		# We use request.POST.get('<variable>') as opposed to request.POST['<variable>'],
		# because the request.POST.get('<variable>') returns None, if the value does not exist,
		# while the request.POST['<variable>'] will raise key error exception

		username = request.POST.get('username')
		password = request.POST.get('password')

		# Django auth system to validate details, and return object if True

		user = authenticate(username=username, password=password)

		if user:
			# Check if user account is active
			if user.is_active:
				login(request, user)
				return HttpResponseRedirect('/rango/')
			else:
				# Inactive account
				return HttpResponse("Your Account is Disabled.")
		else:
			# Incorrect details. 
			print "Invalid login details: {0}, {1}".format(username, password)
			return HttpResponse("Invalid login details supplied.")
	else:
		# Not a POST request
		return render(request, 'rango/login.html', {})


@login_required		
def user_logout(request):
	# logging out the user.
	logout(request)

	# After loggin them out redirect to the homepage. 
	return HttpResponseRedirect('/rango/')

def search(request):
	result_list=[]

	if request.method=='POST':
		query = request.POST['query'].strip()

		if query:
			result_list=run_query(query)

	return render(request, 'rango/search.html', {'result_list': result_list})

def track_url(request):
	if request.method == 'GET':


		## Lesson, Always assign a variable to a default value if you reference it later.
		page_id = None
		url = '/rango/'


		if 'page_id' in request.GET:

			# Getting page_id from the GET request.
			page_id = request.GET['page_id']


			## Lesson, if there is no object found it will return an error!! So put in try except block
			# Page object on the basis of page_id
			try:
				page_object = Page.objects.get(id=page_id)

				# Incrementing the views counter
				page_object.views += 1

				# Saving the values.
				page_object.save()
				url = page_object.url
			except:
				pass

	return HttpResponseRedirect(url)