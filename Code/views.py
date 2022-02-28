import re
from django.core import mail
from django.shortcuts import redirect, render
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth import authenticate,logout, login as auth_login

from django.contrib.auth.models import User
from .models import Profile
import uuid
from website.settings import *
from django.contrib.auth.decorators import login_required
import requests

from datetime import datetime, timedelta
import pandas as pd
import pandas_datareader as pdr
import plotly.graph_objects as go
import plotly


CRYPTOS = ['BTC', 'ETH', 'LTC', 'XRP']
CURRENCY = 'GBP'

# Create your views here.
@login_required(login_url= LOGIN_REDIRECT_URL)
def index(request):
    return render(request, 'index.html')


def signUp(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            if User.objects.filter(username=username).first():
                messages.warning(request, 'Username already taken!')
                return redirect('/signup')
            if User.objects.filter(email=email).first():
                messages.warning(request, 'Email already taken!')
                return redirect('/signup')
            
            user_obj = User.objects.create_user(username=username, email=email, password=password)

            # you can use at time of forgot password.
            # user_obj.set_password('newpassword)
            auth_token=str(uuid.uuid4())
            profile_obj = Profile.objects.create(user=user_obj, auth_token=auth_token)
        
            # send_mail
            msg = send_mail(
                subject = 'Activate your account',
                message = f'Here is the message click on the link to activate http://127.0.0.1:8000/verify/{auth_token}',
                from_email = EMAIL_HOST_USER,
                recipient_list = [email],
                fail_silently=False,
            )

            user_obj.save()
            profile_obj.save()

            print('Mail sent successfully')
            messages.success(request, "Account created successfully")
            return redirect('/token')

        except Exception as e:
            print(e)
            return redirect('/error')

        
    return render(request, 'signUp.html')


def login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user_obj = User.objects.filter(username = username).first()

        if user_obj is None:
            messages.warning(request, "User not found")
            return redirect("/login")     

        profile_obj = Profile.objects.filter(user = user_obj).first()

        if not profile_obj.verified:
            messages.warning(request, "Profile not verified, check your mail.")
            return redirect("/login")

        user = authenticate(username=username, password=password)
        if user is None:
            messages.warning(request, "Invalid Credentials")
            return redirect("/login")

        auth_login(request, user)
        return redirect("/")
    return render(request, 'login.html')


def send_token(request):
    return render(request, 'send_token.html')


def verify(request, slug):
    try:
        profile_obj = Profile.objects.filter(auth_token = slug).first()
        if profile_obj:
            if profile_obj.verified:
                messages.success(request, 'Account already verified')
                return redirect('/login')

            profile_obj.verified = True
            profile_obj.save()
            messages.success(request, 'Your account is now verified')
            return redirect('/login')
        else:
            return redirect('/error')
        
    except Exception as e:
        print(e)
        return redirect('/error')


def error(request):
    return render(request, "error.html")

    
def logoutUser(requests):
    logout(requests)
    messages.success(requests, 'Logged out successfully')
    return redirect('/login')

def forgetPassword(request):
    if request.method == "POST":
        email = request.POST.get('email')
    
        try:
            userObj = User.objects.filter(email=email).first()
            if userObj is None:
                messages.warning(request, "User not found")
                return redirect("/login")

            profileObj = Profile.objects.filter(user = userObj).first()
            if profileObj is None:
                messages.warning(request, "Internal Error")
                return redirect('/error')

            token = profileObj.auth_token
            msg = send_mail(
                subject = 'Reset your Password',
                message = f'Follow this link to reset your password http://127.0.0.1:8000/reset/{token}',
                from_email = EMAIL_HOST_USER,
                recipient_list = [email],
                fail_silently=False,
            )

            if msg==1:
                return render(request, "mail_forgetPass.html")
            else:
                messages.warning(request, "Something went wrong! Try again later.")
                return redirect('/error')

        except Exception as e:
            print(e)
            return redirect('/error')

    return render(request, "forgetPass.html")


def reset(request, token):
    try:
        if request.method == "POST":
            new_password = request.POST.get('password1')
            confirm_password = request.POST.get('password2')

            if new_password == confirm_password:
                # print(confirm_password)

                profile_obj = Profile.objects.filter(auth_token = token).first()
                
                if profile_obj is None:
                    messages.warning(request, "Something went wrong!")
                    return redirect("/error") 

                user_id = profile_obj.user.id

                if user_id is None:
                    messages.warning(request, "User not found :(")
                    return redirect("/login")

                user_obj = User.objects.get(id = user_id)
                user_obj.set_password(new_password)
                user_obj.save()

                messages.success(request, "Password updated successfully :)")
                return redirect("/login")

            else:
                messages.warning(request, "Passwords doesn't match, enter again")


        # if user_obj:
            # print(user_obj.username)
        #     if profile_obj.verified:
        #         messages.success(request, 'Account already verified')
        #         return redirect('/login')

        #     profile_obj.verified = True
        #     profile_obj.save()
        #     messages.success(request, 'Your account is now verified')
        #     return redirect('/login')
        # else:
        #     return redirect('/error')
        
    except Exception as e:
        print(e)
        # return redirect('/error')

    return render(request, 'PassInput.html')

def coinup(request):
    data_url = 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false'
    raw_data = requests.get(data_url).json()

    return render(request, 'crypto/list.html', context={'datas': raw_data})

def getData(cryptocurrency):
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    last_year_date = (now - timedelta(days=365)).strftime("%Y-%m-%d")
    start = pd.to_datetime(last_year_date)
    end = pd.to_datetime(current_date)
    data = pdr.get_data_yahoo(f'{cryptocurrency}-{CURRENCY}', start, end)
    return data

# def graph(request):
#     x_data = [0,1,2,3]
#     y_data = [x**2 for x in x_data]
#     plot_div = plot([Scatter(x=x_data, y=y_data,
#                         mode='lines', name='test',
#                         opacity=0.8, marker_color='green')],
#                output_type='div')
#     return render(request, "crypto/graph.html", context={'plot_div': plot_div})

def graph(request):
    crypto_data = {crypto:getData(crypto) for crypto in CRYPTOS}
    fig = go.Figure()
    for idx, name in enumerate(crypto_data):
        fig = fig.add_trace(
            go.Scatter(
                x = crypto_data[name].index,
                y = crypto_data[name].Close,
                name = name,
            )
        )
    fig.update_layout(
        title = 'Crypto Prices',
        xaxis_title = 'Date',
        yaxis_title = f'Closing price ({CURRENCY})',
        legend_title = 'Cryptocurrencies'
    )
    fig.update_yaxes(type='log', tickprefix='£')
    
    graph_div = plotly.offline.plot(fig, auto_open = False, output_type="div")

    return render(request, "crypto/graph.html", context={'graph_div': graph_div})