# -*- coding: utf-8 -*-
import json
from django.contrib import auth
from django.db.models import Sum
from django.utils.translation import ugettext as _
from django.utils import translation
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.core import serializers
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.generic import View, FormView
from frontsite.decorators import anonymous_required, login_required
from frontsite.forms import UserForm, LoginForm, CategoryForm, AvatarForm, RhymeForm
from frontsite import models
from frontsite import utils

class Index(View):
    template_name = 'frontsite/index.html'

    @method_decorator(login_required)
    def get(self, request):
        print '>>>>', _('klucz')
        return render(request, self.template_name)

class Rhyme(FormView):
    template_name = 'frontsite/rhyme.html'

    def find_data(self):
        return models.Rhyme.objects.all().annotate(vote_strength=Sum('votes__strength')).order_by('-created')

    @method_decorator(login_required)
    def post(self, *args, **kwargs):
        form = RhymeForm(self.request.POST)
        if form.is_valid():
            rhyme = form.save(commit=False)
            if self.kwargs.has_key('id'):
                rhyme.id = self.kwargs['id']
            rhyme.author = self.request.user.profile
            rhyme.save()
            rhyme.profiles.add(self.request.user.profile)
            return  redirect(reverse('frontsite:index'))
        return render(self.request, self.template_name, {
            'form': form,
            'rhymes': self.find_data(),
            'rhymesAuthor': self.request.user.profile.created_rhymes,
            'rhymesStored': self.request.user.profile.stored_rhymes
        })

    def get(self, *args, **kwargs):
        rhyme, rhymesAuthor, rhymesStored = (None, None, None)
        if hasattr(self.request.user, 'profile'):
            rhymesAuthor, rhymesStored = (self.request.user.profile.created_rhymes, self.request.user.profile.stored_rhymes)
        if self.kwargs.has_key('id'):
            rhyme = models.Rhyme.objects.get(pk=self.kwargs['id'])
            if self.kwargs.has_key('delete') and self.kwargs['delete'] == 'delete':
                rhyme.delete()
                return redirect(reverse('frontsite:index'))
        return render(self.request, self.template_name, {
            'form': RhymeForm(instance=rhyme),
            'rhymes': self.find_data(),
            'rhymesAuthor': rhymesAuthor,
            'rhymesStored': rhymesStored
        })

class Category(FormView):

    def find_data(self):
        return models.Category.objects.all().order_by('-id')

    def find_detail(self):
        result = None
        if self.kwargs.has_key('id'):
            result = models.Category.objects.get(pk=self.kwargs['id'])
        return result

    @method_decorator(login_required)
    def post(self, *args, **kwargs):
        form = CategoryForm(self.request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            if self.kwargs.has_key('id'):
                category.id = self.kwargs['id']
            category.save()
            return redirect(reverse('frontsite:category'))
        return render(self.request, 'frontsite/category.html', {
            'form' : form,
            'category': self.find_detail(),
            'categories': self.find_data()
        })

    def get(self, *args, **kwargs):
        category = None
        if self.kwargs.has_key('id'):
            category = models.Category.objects.get(pk=self.kwargs['id'])
            if self.kwargs.has_key('delete') and self.kwargs['delete'] == 'delete':
                category.delete()
                return redirect(reverse('frontsite:category'))
        return render(self.request, 'frontsite/category.html', {
            'form' : CategoryForm(instance=category),
            'category': self.find_detail(),
            'categories': self.find_data()
        })

def avatar(request):
    avatar = models.Avatar()
    avatar.path = utils.handle_uploaded_file(request.FILES['file'], request.POST['user_id'])
    avatar.name = request.POST['user_id']
    #avatar.file = request.FILES['file']
    if request.user.profile.avatar is not None:
        request.user.profile.avatar.delete()
    avatar.profile = request.user.profile
    avatar.save()
    return redirect(reverse('frontsite:user', kwargs={'id': request.POST['user_id']}))

def show_avatar(request, path):
    response = HttpResponse(content_type = "application/octet-stream")
    with open(path, 'r') as f: response.content = f.read()
    return response

class User(View):
    template_name = 'frontsite/user.html'

    @method_decorator(login_required)
    def get(self, *args, **kwargs):
        user = auth.models.User.objects.get(pk=self.kwargs.get('id'))
        votes = None
        if hasattr(user, 'profile'):
            votes = models.VoteUserProfile.objects.filter(user_profile=user.profile).order_by('-date')
        return render(self.request, self.template_name, {
            'user': user,
            'votes': votes,
            'votes_strength_count': votes.aggregate(Sum('strength'))['strength__sum'],
            'avatarForm': AvatarForm()
        })

def get_all_users(request):
    return render(request, 'frontsite/all_users.html', {
        'users' : auth.models.User.objects.all().annotate(vote_strength=Sum('profile__votes__strength'))
    })

class Locale(View):
    def get(self, request, lang):
        if self.kwargs['lang'] != None:
            translation.activate(self.kwargs['lang'])
        return redirect(reverse('frontsite:index'))

def token(request):
    return HttpResponse(_('klucz') + request.COOKIES.get('csrftoken'))

class Logout(View):
    template_name = 'frontsite/logout.html'
    def get(self, request):
        logout(request)
        return redirect(reverse('frontsite:index'))

class Login(FormView):
    model = User
    template_name = 'frontsite/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('frontsite:index')

    def form_valid(self, form):
        auth.login(self.request, form.user)
        if hasattr(self.request.user, 'profile') == False:
            self.request.user.profile = models.UserProfile()
            self.request.user.profile.save()
            self.request.user.save()
        return super(Login, self).form_valid(form)

    @method_decorator(anonymous_required)
    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data(form=self.form_class()))

class Registration(FormView):
    model = User
    template_name = 'frontsite/registration.html'
    form_class = UserForm
    success_url = reverse_lazy('frontsite:index')

    def form_valid(self, form):
        form.save()
        return super(Registration, self).form_valid(form)

    @method_decorator(anonymous_required)
    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data(form=self.form_class()))

def vote(request, profile_id):
    profile = models.UserProfile.objects.get(pk=profile_id)
    if profile and hasattr(request.user, 'profile'):
        vote = models.VoteUserProfile.objects.filter(author__id=request.user.profile.id, user_profile__id=profile.id)
        if not vote:
            vote = models.VoteUserProfile()
            vote.author, vote.user_profile, vote.strength = (request.user.profile, profile, 1)
            vote.save()
    return redirect(reverse('frontsite:all_users'))


def vote_rhyme(request, rhyme_id):
    vote = models.VoteRhyme.objects.filter(author__id=request.user.profile.id, rhyme__id=rhyme_id)
    if not vote:
        vote = models.VoteRhyme()
        vote.author, vote.rhyme, vote.strength = (request.user.profile, models.Rhyme.objects.get(pk=rhyme_id), 1)
        vote.save()
    return redirect(reverse('frontsite:index'))

def rhyme_store(request, id):
    rhyme = models.Rhyme.objects.get(pk=id)
    #if rhyme.id  not in request.user.profile.stored_rhymes:
    if models.UserProfile.objects.filter(pk=request.user.profile.id, stored_rhymes__in=[rhyme.id]) is not None:
        request.user.profile.stored_rhymes.add(rhyme)
        request.user.profile.save()
        print 'add here'
    print 'yupi'
