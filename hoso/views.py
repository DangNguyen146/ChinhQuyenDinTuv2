from .models import Category, Field, FileHoSo, Comment, NopHoSo, StatusHoSo
from authentication.models import User
from .serializers import CategorySerializer, FieldSerializer, FileSerializer, FileDetailSerializer, UserSerializer, ActionSerializer, CommentSerializer, MyNopDonSerializer, StatusHoSoSerializer, StatusHoSoSerializer
from .paginator import BasePaginator

from django.http import Http404
from django.conf import settings
from django.db.models import F

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

class CategoryViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class  = CategorySerializer


class FieldViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveAPIView):
    serializer_class = FieldSerializer


    def get_queryset(self):
        fields = Field.objects.filter(active=True)

        q = self.request.query_params.get('q')
        if q is not None:
            fields = fields.filter(title__icontains=q)
        
        cate_id = self.request.query_params.get('category_id')
        if cate_id is not None:
            fields = fields.filter(category_id=cate_id)
        return fields

    @action(methods=['get'], detail=True, url_path="files")
    def get_files(self, request, pk):
        files = Field.objects.get(pk=pk).files.filter(active=True)

        kw = request.query_params.get('kw')
        if kw is not None:
            files = files.filter(title__icontains=kw)

        return Response(FileSerializer(files, many=True).data, status=status.HTTP_200_OK)

class FileHoSoViewSet(viewsets.ViewSet,  generics.ListAPIView, generics.RetrieveAPIView):
    queryset = FileHoSo.objects.filter(active=True)
    serializer_class  = FileDetailSerializer

    def get_queryset(self):
        hosos = FileHoSo.objects.filter(active=True)

        q = self.request.query_params.get('q')
        if q is not None:
            hosos = hosos.filter(title__icontains=q)
        
        field_id = self.request.query_params.get('field_id')
        if field_id is not None:
            hosos = hosos.filter(field_id=field_id)
        return hosos
 



class UserViewSet(viewsets.ViewSet, generics.CreateAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class  = UserSerializer

    def get_permissions(self):
        if self.action in ['add_comment', 'take_action', 'get_current_user']:
            return [permissions.IsAuthenticated()]
        
        return [permissions.AllowAny()]

    @action(methods=['get'], detail=False, url_path='current-user')
    def get_current_user(self, request):
        return Response(self.serializer_class(request.user).data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path="checkfile")
    def take_action(self, request, pk):
        content = request.data.get('content')
        try:
            action_type = int(request.data['type'])
        except IndexError | ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            action = Action.objects.create(type=action_type, creator= request.user, card=self.get_object())

            return Response(ActionSerializer(action).data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path="add-comment")
    def add_comment(self, request, pk):
        content = request.data.get('content')
        if content:
           c = Comment.objects.create(content=content, card=self.get_object(), creator= request.user)
           return Response(CommentSerializer(c).data, status=status.HTTP_201_CREATED)
        
        return Response(status=status.HTTP_400_BAD_REQUEST)




class NopHoSoViewSet(viewsets.ViewSet):
    queryset = NopHoSo.objects.all()
    serializer_class  = MyNopDonSerializer

    def get_permissions(self):
        if self.action in ['nop_hoso']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    @action(methods=['post'], detail=False, url_path="nop_hoso")
    def nop_hoso(self, request):
        serializer = MyNopDonSerializer(data=request.data)
        if serializer.is_valid():
            c = serializer.save(user=request.user)
            StatusHoSo.objects.create(user=request.user, hosonop=c)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StatusHoSoViewSet(viewsets.ViewSet):
    queryset = StatusHoSo.objects.all()
    serializer_class  = StatusHoSoSerializer

    def get_permissions(self):
        if self.action in ['getstatus_user']:
            return [permissions.IsAuthenticated()]
        
        return [permissions.AllowAny()]

    @action(methods=['get'], detail=False, url_path='getstatus')
    def getstatus_user(self, request, format=None):
        statuss = StatusHoSo.objects.filter(user=request.user)
        serializer = StatusHoSoSerializer(statuss, many=True)
        return Response(serializer.data)