"""
Forms and validation code for user registration.

"""


from django.contrib.auth.models import User
from django import forms
from django.utils.translation import ugettext_lazy as _


# I put this on all required fields, because it's easier to pick up
# on them with CSS or JavaScript if they have a class of "required"
# in the HTML. Your mileage may vary. If/when Django ticket #3515
# lands in trunk, this will no longer be necessary.
attrs_dict = {'class': 'required'}


class RegistrationForm(forms.Form):
    """
    Form for registering a new user account.
    
    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.
    
    Subclasses should feel free to add any additional validation they
    need, but should avoid defining a ``save()`` method -- the actual
    saving of collected user data is delegated to the active
    registration backend.
    
    """
    username = forms.RegexField(regex=r'^[\w.@+-]+$',
                                max_length=30,
                                widget=forms.TextInput(attrs=attrs_dict),
                                label=_("Username"),
                                error_messages={'invalid': _("This value may contain only letters, numbers and @/./+/-/_ characters.")})
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict,
                                                               maxlength=75)),
                             label=_("E-mail"))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_("Password (again)"))
    
    def clean_username(self):
        """
        Validate that the username is alphanumeric and is not already
        in use.
        
        """
        existing = User.objects.filter(username__iexact=self.cleaned_data['username'])
        if existing.exists():
            raise forms.ValidationError(_("A user with that username already exists."))
        else:
            return self.cleaned_data['username']

    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.
        
        """
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_("The two password fields didn't match."))
        return self.cleaned_data


class RegistrationFormTermsOfService(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which adds a required checkbox
    for agreeing to a site's Terms of Service.
    
    """
    tos = forms.BooleanField(widget=forms.CheckboxInput(attrs=attrs_dict),
                             label=_(u'I have read and agree to the Terms of Service'),
                             error_messages={'required': _("You must agree to the terms to register")})


class RegistrationFormUniqueEmail(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which enforces uniqueness of
    email addresses.
    
    """
    def clean_email(self):
        """
        Validate that the supplied email address is unique for the
        site.
        
        """
        if User.objects.filter(email__iexact=self.cleaned_data['email']):
            raise forms.ValidationError(_("This email address is already in use. Please supply a different email address."))
        return self.cleaned_data['email']

class RegistrationFormNoUserName(RegistrationFormUniqueEmail):
    """
    Based on http://djangosnippets.org/snippets/686/ with modifications by Cole Krumbholz
    
    A registration form that only requires the user to enter their e-mail 
    address and password. The username is automatically generated
    This class requires django-registration to extend the 
    RegistrationFormUniqueEmail.
    
    """ 
    username = forms.CharField(widget=forms.HiddenInput, max_length=75, required=False)

    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict, maxlength=75)),
                             label=_("E-mail"))

    first_name = forms.CharField(widget=forms.TextInput(attrs=dict(attrs_dict, maxlength=30)))

    last_name = forms.CharField(widget=forms.TextInput(attrs=dict(attrs_dict, maxlength=30)))

    def clean_username(self):
        "This function is required to overwrite an inherited username clean"
        return self.cleaned_data['username']

    def clean(self):
        if not self.errors:
            # originally this snipped shortened the username using the following encoding of the email:
            #
            # self.cleaned_data['username'] = '%s%s' % (self.cleaned_data['email'].split('@',1)[0], User.objects.count())
            #
            # In my limited testing I have not found a problem with usernames > 30 characters long
            # so I simply use the email for the username:
            self.cleaned_data['email'] = self.cleaned_data['email'].strip().lower()
            self.cleaned_data['username'] = self.cleaned_data['email']
            
        super(RegistrationFormNoUserName, self).clean()
        return self.cleaned_data

    def __init__(self, *args, **kwargs):
        # reorder the fields
        # see discussion at http://stackoverflow.com/questions/913589/django-forms-inheritance-and-order-of-form-fields
        
        super(RegistrationFormNoUserName, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['email', 'password1', 'password2']


class RegistrationFormNoUserNameWithFirstLast(RegistrationFormNoUserName):
    first_name = forms.CharField(widget=forms.TextInput(attrs=dict(attrs_dict, maxlength=30)))

    last_name = forms.CharField(widget=forms.TextInput(attrs=dict(attrs_dict, maxlength=30)))

    def __init__(self, *args, **kwargs):
        # reorder the fields
        # see discussion at http://stackoverflow.com/questions/913589/django-forms-inheritance-and-order-of-form-fields
        
        super(RegistrationFormNoUserName, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['email', 'first_name', 'last_name', 'password1', 'password2']


class RegistrationFormNoFreeEmail(RegistrationForm):
    """
    Subclass of ``RegistrationForm`` which disallows registration with
    email addresses from popular free webmail services; moderately
    useful for preventing automated spam registrations.
    
    To change the list of banned domains, subclass this form and
    override the attribute ``bad_domains``.
    
    """
    bad_domains = ['aim.com', 'aol.com', 'email.com', 'gmail.com',
                   'googlemail.com', 'hotmail.com', 'hushmail.com',
                   'msn.com', 'mail.ru', 'mailinator.com', 'live.com',
                   'yahoo.com']
    
    def clean_email(self):
        """
        Check the supplied email address against a list of known free
        webmail domains.
        
        """
        email_domain = self.cleaned_data['email'].split('@')[1]
        if email_domain in self.bad_domains:
            raise forms.ValidationError(_("Registration using free email addresses is prohibited. Please supply a different email address."))
        return self.cleaned_data['email']


class EmailOnlyAuthenticationForm(AuthenticationForm):
    """
    Subclass of django.contrib.auth.AuthenticationForm that accepts
    emails for usernames
    """
    username = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict, maxlength=75)), 
                                label=_("E-mail / Username"))
