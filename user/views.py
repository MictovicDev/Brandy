from django.shortcuts import render
from rest_framework import generics,status,views
from .serializers import RegisterSerializer,EmailVerificationSerializer, LoginSerializer
from rest_framework.response import Response
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from user.utils import Util
import jwt
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import User


# Create your views here.

class RegisterView(generics.GenericAPIView):

    serializer_class = RegisterSerializer
    def post(self, request):
        data = request.data
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user_data = serializer.data
        user = User.objects.get(email=user_data['email'])
        token = RefreshToken.for_user(user).access_token
        current_site = get_current_site(request).domain
        relativeLink = reverse('email-verify')
        absurl = 'http://' + current_site + relativeLink + '?token=' + str(token)
        email_body = 'Hi' + ' ' + user.username + ' ' + 'Use the Link below to verify your email\n' + absurl
        data = {'email_body': email_body, 'subject':'Verify your Account', 'to_email': user.email}
        Util.send_email(data)

        return Response(user_data, status=status.HTTP_201_CREATED)

class VerifyEmail(views.APIView):
    serializer_class = EmailVerificationSerializer

    token_param_config=openapi.Parameter('token',in_=openapi.IN_QUERY, description='Description', type=openapi.TYPE_STRING)
    @swagger_auto_schema(manual_parameters=[token_param_config])
    def get(self, request):
        token = request.GET.get('token')
        try:
            payload = jwt.decode(token,settings.SECRET_KEY,algorithms=['HS256'])
            user = User.objects.get(id=payload['user_id'])
            if not user.is_verified:
                user.is_verified = True
                user.save()
                # data = {'email_body': 'Congratulations your account has been activated', 'subject':'Your Account has been verified', 'to_email': user.email}
                # Util.send_confirmation(data)
                return Response({'email':'Succefully activated'}, status=status.HTTP_201_CREATED)
        except jwt.ExpiredSignatureError as identifier:
            return Response({'error':'Activation Expired'}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.exceptions.DecodeError as identifier:
            return Response({'error':'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        
class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data, status=status.HTTP_200_OK)



