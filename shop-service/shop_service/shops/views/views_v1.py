import httpx
import os
from django.conf import settings
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from ..models import * 
from ..serializers import *
from utils.pagination import CustomPagination
from shop_service.authentication import GatewayHeaderAuthentication
from shop_service.messaging import publisher


__all__ = [
    'ShopListAPIView',
    'ShopDetailWithSlugAPIView',
    'ShopDetailWithUuidAPIView',
    'ShopCreateAPIView',
    'ShopManagementAPIView',
    'UserShopAPIView',
    'ShopBranchListByShopAPIView',
    'ShopBranchDetailAPIView',
    'CreateShopBranchAPIView',
    'ShopBranchManagementAPIView',
    'CommentListByShopAPIView',
    'CreateShopCommentAPIView',
    'CommentManagementAPIView',
    'ShopMediaByShopAPIView',
    'CreateShopMediaAPIView',
    'DeleteShopMediaAPIView',
    'ShopSocialMediaListByShopAPIView',
    'ShopSocialMediaDetailAPIView',
    'CreateShopSocialMediaAPIView',
    'ShopSocialMediaManagementAPIView',
]

# Shop Views
class ShopListAPIView(APIView):
    """List all active shops with pagination."""
    http_method_names =['get']
    pagination_class = CustomPagination

    def get(self, request):
        pagination = self.pagination_class()
        shops = Shop.objects.filter(is_active=True)
        paginated_shops = pagination.paginate_queryset(shops, request)
        if paginated_shops:
            serializer = ShopListSerializer(paginated_shops, many=True)
            return pagination.get_paginated_response(serializer.data)
        
        return Response({'error': 'Shops not found'}, status=status.HTTP_404_NOT_FOUND)


class ShopDetailWithSlugAPIView(APIView):
    """Retrieve details of a specific shop by slug."""
    http_method_names =['get']

    def get(self, request, shop_slug):
        shop = get_object_or_404(Shop, slug=shop_slug, is_active=True)
        serializer = ShopDetailSerializer(shop)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ShopDetailWithUuidAPIView(APIView):
    """Retrieve details of a specific shop by uuid."""
    http_method_names =['get']

    def get(self, request, shop_uuid):
        shop = get_object_or_404(Shop, id=shop_uuid, is_active=True)
        serializer = ShopDetailSerializer(shop)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ShopCreateAPIView(APIView):
    """Create a new shop. Only authenticated users can create."""
    http_method_names = ['post']
    permission_classes = [IsAuthenticated]
    authentication_classes = [GatewayHeaderAuthentication]

    def post(self, request):
        user = request.user
        data = request.data.copy()  
        data['user'] = str(user.id)  
        serializer = ShopCreateUpdateSerializer(data=data)
        if serializer.is_valid():
            shop = serializer.save()
            try:
                publisher.publish_shop_created(
                    user_uuid=str(user.id),
                    shop_id=str(shop.id)
                )
            except Exception as e:
                print(f"⚠️ Failed to publish shop.created event: {e}")

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShopManagementAPIView(APIView):
    """Update or soft-delete a shop. Only the owner can modify or delete."""
    http_method_names = ['patch', 'delete']
    permission_classes = [IsAuthenticated]
    authentication_classes = [GatewayHeaderAuthentication]

    def patch(self, request, shop_slug):
        user = request.user
        data = request.data.copy()  
        data['user'] = str(user.id)
        shop = get_object_or_404(Shop, slug=shop_slug, is_active=True)
        if str(shop.user) != str(user.id):
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ShopCreateUpdateSerializer(shop, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
    
    
    def delete(self, request, shop_slug):
        user = request.user
        shop = get_object_or_404(Shop, slug=shop_slug, is_active=True)
        if str(shop.user) != str(user.id):
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
        
        shop.is_active = False
        shop.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserShopAPIView(APIView):
    permission_classes = [AllowAny]
    http_method_names = ['get']

    def get(self, request, user_id):
        try:
            shop = Shop.objects.filter(user=user_id, is_active=True).first()
            if not shop:
                return Response({'error': 'User has no active shop'}, status=status.HTTP_404_NOT_FOUND)
            serializer = ShopDetailSerializer(shop)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Internal server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

# ShopBranch Views    
class ShopBranchListByShopAPIView(APIView):
    """Returns a list of active branches for a given shop."""
    http_method_names = ['get']

    def get(self, request, shop_slug):
        shop = get_object_or_404(Shop, slug=shop_slug, is_active=True)
        shop_branches = ShopBranch.objects.filter(shop=shop, is_active=True)
        if shop_branches.exists():
            serializer = ShopBranchListSerializer(shop_branches, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(
            {'detail': 'No active branches found for this shop.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


class ShopBranchDetailAPIView(APIView):
    """Returns detailed information about a specific branch by its slug."""
    http_method_names =['get']

    def get(self, request, shop_branch_slug):
        shop_branch = get_object_or_404(ShopBranch, slug=shop_branch_slug, is_active=True)
        serializer = ShopBranchDetailSerializer(shop_branch)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class CreateShopBranchAPIView(APIView):
    """Allows an authenticated user to create a new shop branch."""
    http_method_names =['post']
    permission_classes = [IsAuthenticated]
    authentication_classes = [GatewayHeaderAuthentication]

    def post(self, request, shop_slug):
        user = request.user
        data = request.data.copy()  
        data['user'] = str(user.id)
        shop = get_object_or_404(Shop, slug=shop_slug, is_active=True)
        if str(shop.user) != str(user.id):
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ShopBranchCreateUpdateSerializer(
            data=data, context={
                'request': request,
                'shop': shop
        })
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShopBranchManagementAPIView(APIView):
    """Allows the owner to update or soft-delete their shop branch."""
    http_method_names = ['patch', 'delete']
    permission_classes = [IsAuthenticated]
    authentication_classes = [GatewayHeaderAuthentication]

    def patch(self, request, shop_branch_slug):
        data = request.data
        shop_branch = get_object_or_404(ShopBranch, slug=shop_branch_slug, is_active=True)
        if str(shop_branch.shop.user) != str(request.user.id):
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ShopBranchCreateUpdateSerializer(shop_branch, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
    

    def delete(self, request, shop_branch_slug):
        shop_branch = get_object_or_404(ShopBranch, slug=shop_branch_slug, is_active=True)
        if str(shop_branch.shop.user) != str(request.user.id):
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
        
        shop_branch.is_active = False
        shop_branch.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ShopComment Views
class CommentListByShopAPIView(APIView):
    """List comments of a shop."""
    pagination_class = CustomPagination
    http_method_names = ['get']

    def get(self, request, shop_slug):
        pagination = self.pagination_class()
        shop = get_object_or_404(Shop.objects.filter(is_active=True), slug=shop_slug)
        comments = ShopComment.objects.filter(shop=shop)
        paginator = pagination.paginate_queryset(comments, request)
        serializer = ShopCommentSerializer(paginator, many=True)

        return pagination.get_paginated_response(serializer.data)


class CreateShopCommentAPIView(APIView):
    """Create a shop comment."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [GatewayHeaderAuthentication]

    def post(self, request, shop_slug):
        user_id = request.user.id 
        data = request.data.copy()  
        data['user'] = str(user_id)   
        shop = get_object_or_404(Shop, slug=shop_slug, is_active=True)

        serializer = ShopCommentSerializer(data=data, context={'shop': shop})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class CommentManagementAPIView(APIView):
    """Update or delete a comment."""
    http_method_names = ['delete', 'patch']
    permission_classes = [IsAuthenticated]
    authentication_classes = [GatewayHeaderAuthentication]

    def patch(self, request, comment_id):
        data = request.data
        comment = get_object_or_404(ShopComment, id=comment_id)
        if str(comment.user) != str(request.user.id):
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ShopCommentSerializer(comment, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    def delete(self, request, comment_id):
        comment = get_object_or_404(ShopComment, id=comment_id)
        if str(comment.user) != str(request.user.id):
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
        
        comment.is_active = False
        comment.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ShopMedia Views
class ShopMediaByShopAPIView(APIView):
    """Returns a media for a given shop."""
    http_method_names = ['get']

    def get(self, request, shop_slug):
        shop = get_object_or_404(Shop, slug=shop_slug, is_active=True)
        social_medias = ShopMedia.objects.filter(shop=shop)
        if social_medias.exists():
            serializer = ShopMediaSerializer(social_medias, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(
            {'detail': 'No media found for this shop.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


class CreateShopMediaAPIView(APIView):
    """Allows an authenticated user to create a new shop media."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [GatewayHeaderAuthentication]

    def post(self, request, shop_slug):
        user = request.user
        data = request.data.copy()  
        data['user'] = str(user.id)
        shop = get_object_or_404(Shop, slug=shop_slug, is_active=True)
        if str(shop.user) != str(user.id):
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ShopMediaSerializer(
            data=data, context={
            'request': request,
            'shop': shop
        })
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteShopMediaAPIView(APIView):
    """Allows the owner to delete their shop media."""
    http_method_names = ['delete']
    permission_classes = [IsAuthenticated]
    authentication_classes = [GatewayHeaderAuthentication]
    
    def delete(self, request, media_id):
        shop_media = get_object_or_404(ShopMedia, id=media_id)
        if str(shop_media.shop.user) != str(request.user.id):
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
        
        shop_media.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ShopScoialMedia Views
class ShopSocialMediaListByShopAPIView(APIView):
    """Returns a list of branches for a given shop."""
    http_method_names = ['get']

    def get(self, request, shop_slug):
        shop = get_object_or_404(Shop, slug=shop_slug, is_active=True)
        social_medias = ShopSocialMedia.objects.filter(shop=shop)
        if social_medias.exists():
            serializer = ShopSocialMediaSerializer(social_medias, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(
            {'detail': 'No social media found for this shop.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


class ShopSocialMediaDetailAPIView(APIView):
    """Returns detailed information about a specific social media by its id."""
    http_method_names = ['get']
    
    def get(self, request, social_media_id):
        social_media = get_object_or_404(ShopSocialMedia, id=social_media_id)
        serializer = ShopSocialMediaSerializer(social_media)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class CreateShopSocialMediaAPIView(APIView):
    """Allows an authenticated user to create a new shop social media."""
    http_method_names = ['post']
    permission_classes = [IsAuthenticated]
    authentication_classes = [GatewayHeaderAuthentication]

    def post(self, request, shop_slug):
        user = request.user
        data = request.data.copy()  
        data['user'] = str(user.id)
        shop = get_object_or_404(Shop, slug=shop_slug, is_active=True)
        if str(shop.user) != str(user.id):
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ShopSocialMediaSerializer(
            data=data, context={
                'request': request,
                'shop': shop
        })
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShopSocialMediaManagementAPIView(APIView):
    """Allows the owner to update or delete their shop social media."""
    http_method_names = ['patch', 'delete']
    permission_classes = [IsAuthenticated]
    authentication_classes = [GatewayHeaderAuthentication]

    def patch(self, request, social_media_id):
        data = request.data
        social_media = get_object_or_404(ShopSocialMedia, id=social_media_id)
        if str(social_media.shop.user) != str(request.user.id):
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ShopSocialMediaSerializer(social_media, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, social_media_id):
        social_media = get_object_or_404(ShopSocialMedia, id=social_media_id)
        if str(social_media.shop.user) != str(request.user.id):
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
        
        social_media.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        