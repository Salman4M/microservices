import httpx
import os
import logging
from typing import List
from django.conf import settings
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from ..models import * 
from ..serializers import *
from utils.pagination import CustomPagination
from utils.order_client import order_client
from shop_service.authentication import GatewayHeaderAuthentication
from shop_service.messaging import publisher

logger = logging.getLogger('shop_service')


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
    'ShopOrderItemListAPIView',
    'ShopOrderItemDetailAPIView',
    'ShopOrderItemStatusUpdateAPIView',
]

# Shop Views
class ShopListAPIView(APIView):
    """List all active shops with pagination."""
    http_method_names =['get']
    pagination_class = CustomPagination

    def get(self, request):
        pagination = self.pagination_class()
        shops = Shop.objects.filter(is_active=True, status=Shop.APPROVED)
        paginated_shops = pagination.paginate_queryset(shops, request)
        if paginated_shops:
            serializer = ShopListSerializer(paginated_shops, many=True)
            return pagination.get_paginated_response(serializer.data)
        
        return Response({'error': 'Shops not found'}, status=status.HTTP_404_NOT_FOUND)


class ShopDetailWithSlugAPIView(APIView):
    """Retrieve details of a specific shop by slug."""
    http_method_names =['get']

    def get(self, request, shop_slug):
        shop = get_object_or_404(Shop, slug=shop_slug, is_active=True, status=Shop.APPROVED)
        serializer = ShopDetailSerializer(shop)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ShopDetailWithUuidAPIView(APIView):
    """Retrieve details of a specific shop by uuid."""
    http_method_names =['get']

    def get(self, request, shop_uuid):
        shop = get_object_or_404(Shop, id=shop_uuid, is_active=True, status=Shop.APPROVED)
        serializer = ShopDetailSerializer(shop)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ShopCreateAPIView(APIView):
    """Create a new shop. Only authenticated users can create."""
    http_method_names = ['post']
    permission_classes = [IsAuthenticated]
    authentication_classes = [GatewayHeaderAuthentication]

    @extend_schema(
        operation_id='shop_create',
        summary='Create a new shop',
        description='Create a new shop. Only authenticated users can create shops.',
        tags=['Shop'],
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'name': {
                        'type': 'string',
                        'description': 'Shop name'
                    },
                    'about': {
                        'type': 'string',
                        'description': 'Shop description'
                    },
                    'profile': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Shop profile image (optional)'
                    }
                },
                'required': ['name']
            }
        },
        responses={201: ShopCreateUpdateSerializer, 400: None},
    )
    
    def post(self, request):
        user = request.user
        logger.info(f"POST /create/ - Shop creation request from user {user.id}")
        if Shop.objects.filter(user=user.id).first():
            logger.warning(f"POST /create/ - User {user.id} already has a shop")
            return Response({'error': 'You already have Shop'}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()  
        data['user'] = str(user.id)  
        serializer = ShopCreateUpdateSerializer(data=data)
        if serializer.is_valid():
            shop = serializer.save(user=user.id)  
            logger.info(f"POST /create/ - Shop {shop.id} created successfully by user {user.id} with status {shop.status}")

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        logger.warning(f"POST /create/ - Validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShopManagementAPIView(APIView):
    """Update or soft-delete a shop. Only the owner can modify or delete."""
    http_method_names = ['patch', 'delete']
    permission_classes = [IsAuthenticated]
    authentication_classes = [GatewayHeaderAuthentication]

    @extend_schema(
        operation_id='shop_update',
        summary='Update a shop',
        description='Update shop information. Only the shop owner can update.',
        tags=['Shop'],
        parameters=[
            OpenApiParameter(name='shop_slug', type=OpenApiTypes.STR, location=OpenApiParameter.PATH, description='Shop slug')
        ],
        request=ShopCreateUpdateSerializer,
        responses={200: ShopCreateUpdateSerializer, 400: None, 403: None}
    )
    def patch(self, request, shop_slug):
        user = request.user
        logger.info(f"PATCH /shops/{shop_slug}/management/ - Update request from user {user.id}")
        data = request.data.copy()  
        data['user'] = str(user.id)
        shop = get_object_or_404(Shop, slug=shop_slug, is_active=True)
        if str(shop.user) != str(user.id):
            logger.warning(f"PATCH /shops/{shop_slug}/management/ - Permission denied for user {user.id}")
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ShopCreateUpdateSerializer(shop, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"PATCH /shops/{shop_slug}/management/ - Shop {shop.id} updated successfully")
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        logger.warning(f"PATCH /shops/{shop_slug}/management/ - Validation failed: {serializer.errors}")
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
    
    
    @extend_schema(
        operation_id='shop_delete',
        summary='Delete a shop',
        description='Soft delete a shop. Only the shop owner can delete.',
        tags=['Shop'],
        parameters=[
            OpenApiParameter(name='shop_slug', type=OpenApiTypes.STR, location=OpenApiParameter.PATH, description='Shop slug')
        ],
        responses={204: None, 403: None}
    )
    def delete(self, request, shop_slug):
        user = request.user
        logger.info(f"DELETE /shops/{shop_slug}/management/ - Delete request from user {user.id}")
        shop = get_object_or_404(Shop, slug=shop_slug, is_active=True)
        if str(shop.user) != str(user.id):
            logger.warning(f"DELETE /shops/{shop_slug}/management/ - Permission denied for user {user.id}")
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
        
        shop.is_active = False
        shop.save()
        logger.info(f"DELETE /shops/{shop_slug}/management/ - Shop {shop.id} soft-deleted successfully")
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserShopAPIView(APIView):
    """Retrieve the active shop for a specific user"""
    permission_classes = [AllowAny]
    http_method_names = ['get']

    def get(self, request, user_id):
        try:
            shop = Shop.objects.filter(user=user_id, is_active=True, status=Shop.APPROVED).first()
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
        shop = get_object_or_404(Shop, slug=shop_slug, is_active=True, status=Shop.APPROVED)
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

    @extend_schema(
        operation_id='branch_create',
        summary='Create a shop branch',
        description='Create a new branch for a shop. Only the shop owner can create branches.',
        tags=['ShopBranch'],
        parameters=[
            OpenApiParameter(name='shop_slug', type=OpenApiTypes.STR, location=OpenApiParameter.PATH, description='Shop slug')
        ],
        request=ShopBranchCreateUpdateSerializer,
        responses={201: ShopBranchCreateUpdateSerializer, 400: None, 403: None}
    )
    def post(self, request, shop_slug):
        user = request.user
        logger.info(f"POST /branches/{shop_slug}/create/ - Branch creation request from user {user.id}")
        data = request.data.copy()  
        data['user'] = str(user.id)
        shop = get_object_or_404(Shop, slug=shop_slug, is_active=True, status=Shop.APPROVED)
        if str(shop.user) != str(user.id):
            logger.warning(f"POST /branches/{shop_slug}/create/ - Permission denied for user {user.id}")
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ShopBranchCreateUpdateSerializer(
            data=data, context={
                'request': request,
                'shop': shop
        })
        if serializer.is_valid():
            branch = serializer.save()
            logger.info(f"POST /branches/{shop_slug}/create/ - Branch {branch.id} created successfully for shop {shop.id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        logger.warning(f"POST /branches/{shop_slug}/create/ - Validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShopBranchManagementAPIView(APIView):
    """Allows the owner to update or soft-delete their shop branch."""
    http_method_names = ['patch', 'delete']
    permission_classes = [IsAuthenticated]
    authentication_classes = [GatewayHeaderAuthentication]

    @extend_schema(
        operation_id='branch_update',
        summary='Update a shop branch',
        description='Update branch information. Only the shop owner can update.',
        tags=['ShopBranch'],
        parameters=[
            OpenApiParameter(name='shop_branch_slug', type=OpenApiTypes.STR, location=OpenApiParameter.PATH, description='Branch slug')
        ],
        request=ShopBranchCreateUpdateSerializer,
        responses={200: ShopBranchCreateUpdateSerializer, 400: None, 403: None}
    )
    def patch(self, request, shop_branch_slug):
        user = request.user
        logger.info(f"PATCH /branches/{shop_branch_slug}/management/ - Update request from user {user.id}")
        data = request.data
        shop_branch = get_object_or_404(ShopBranch, slug=shop_branch_slug, is_active=True)
        if str(shop_branch.shop.user) != str(request.user.id):
            logger.warning(f"PATCH /branches/{shop_branch_slug}/management/ - Permission denied for user {user.id}")
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ShopBranchCreateUpdateSerializer(shop_branch, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"PATCH /branches/{shop_branch_slug}/management/ - Branch {shop_branch.id} updated successfully")
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        logger.warning(f"PATCH /branches/{shop_branch_slug}/management/ - Validation failed: {serializer.errors}")
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
    

    @extend_schema(
        operation_id='branch_delete',
        summary='Delete a shop branch',
        description='Soft delete a shop branch. Only the shop owner can delete.',
        tags=['ShopBranch'],
        parameters=[
            OpenApiParameter(name='shop_branch_slug', type=OpenApiTypes.STR, location=OpenApiParameter.PATH, description='Branch slug')
        ],
        responses={204: None, 403: None}
    )
    def delete(self, request, shop_branch_slug):
        user = request.user
        logger.info(f"DELETE /branches/{shop_branch_slug}/management/ - Delete request from user {user.id}")
        shop_branch = get_object_or_404(ShopBranch, slug=shop_branch_slug, is_active=True)
        if str(shop_branch.shop.user) != str(request.user.id):
            logger.warning(f"DELETE /branches/{shop_branch_slug}/management/ - Permission denied for user {user.id}")
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
        
        shop_branch.is_active = False
        shop_branch.save()
        logger.info(f"DELETE /branches/{shop_branch_slug}/management/ - Branch {shop_branch.id} soft-deleted successfully")
        return Response(status=status.HTTP_204_NO_CONTENT)


# ShopComment Views
class CommentListByShopAPIView(APIView):
    """List comments of a shop."""
    pagination_class = CustomPagination
    http_method_names = ['get']

    def get(self, request, shop_slug):
        pagination = self.pagination_class()
        shop = get_object_or_404(Shop.objects.filter(is_active=True, status=Shop.APPROVED), slug=shop_slug)
        comments = ShopComment.objects.filter(shop=shop)
        paginator = pagination.paginate_queryset(comments, request)
        serializer = ShopCommentSerializer(paginator, many=True)

        return pagination.get_paginated_response(serializer.data)


class CreateShopCommentAPIView(APIView):
    """Create a shop comment."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [GatewayHeaderAuthentication]

    @extend_schema(
        operation_id='comment_create',
        summary='Create a shop comment',
        description='Create a new comment for a shop. Only authenticated users can create comments.',
        tags=['ShopComment'],
        parameters=[
            OpenApiParameter(name='shop_slug', type=OpenApiTypes.STR, location=OpenApiParameter.PATH, description='Shop slug')
        ],
        request=ShopCommentSerializer,
        responses={201: ShopCommentSerializer, 400: None}
    )
    def post(self, request, shop_slug):
        user_id = request.user.id
        logger.info(f"POST /comments/{shop_slug}/create/ - Comment creation request from user {user_id}")
        data = request.data.copy()  
        data['user'] = str(user_id)   
        shop = get_object_or_404(Shop, slug=shop_slug, is_active=True, status=Shop.APPROVED)

        serializer = ShopCommentSerializer(data=data, context={'shop': shop})
        if serializer.is_valid():
            comment = serializer.save()
            logger.info(f"POST /comments/{shop_slug}/create/ - Comment {comment.id} created successfully by user {user_id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        logger.warning(f"POST /comments/{shop_slug}/create/ - Validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class CommentManagementAPIView(APIView):
    """Update or delete a comment."""
    http_method_names = ['delete', 'patch']
    permission_classes = [IsAuthenticated]
    authentication_classes = [GatewayHeaderAuthentication]

    @extend_schema(
        operation_id='comment_update',
        summary='Update a comment',
        description='Update a comment. Only the comment owner can update.',
        tags=['ShopComment'],
        parameters=[
            OpenApiParameter(name='comment_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='Comment ID')
        ],
        request=ShopCommentSerializer,
        responses={200: ShopCommentSerializer, 400: None, 403: None}
    )
    def patch(self, request, comment_id):
        user = request.user
        logger.info(f"PATCH /comments/{comment_id}/management/ - Update request from user {user.id}")
        data = request.data
        comment = get_object_or_404(ShopComment, id=comment_id)
        if str(comment.user) != str(request.user.id):
            logger.warning(f"PATCH /comments/{comment_id}/management/ - Permission denied for user {user.id}")
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ShopCommentSerializer(comment, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"PATCH /comments/{comment_id}/management/ - Comment {comment.id} updated successfully")
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        logger.warning(f"PATCH /comments/{comment_id}/management/ - Validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    @extend_schema(
        operation_id='comment_delete',
        summary='Delete a comment',
        description='Soft delete a comment. Only the comment owner can delete.',
        tags=['ShopComment'],
        parameters=[
            OpenApiParameter(name='comment_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='Comment ID')
        ],
        responses={204: None, 403: None}
    )
    def delete(self, request, comment_id):
        user = request.user
        logger.info(f"DELETE /comments/{comment_id}/management/ - Delete request from user {user.id}")
        comment = get_object_or_404(ShopComment, id=comment_id)
        if str(comment.user) != str(request.user.id):
            logger.warning(f"DELETE /comments/{comment_id}/management/ - Permission denied for user {user.id}")
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
        
        comment.is_active = False
        comment.save()
        logger.info(f"DELETE /comments/{comment_id}/management/ - Comment {comment.id} soft-deleted successfully")
        return Response(status=status.HTTP_204_NO_CONTENT)


# ShopMedia Views
class ShopMediaByShopAPIView(APIView):
    """Returns a media for a given shop."""
    http_method_names = ['get']

    def get(self, request, shop_slug):
        shop = get_object_or_404(Shop, slug=shop_slug, is_active=True, status=Shop.APPROVED)
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

    @extend_schema(
        operation_id='media_create',
        summary='Create shop media',
        description='Upload media files for a shop. Only the shop owner can upload media.',
        tags=['ShopMedia'],
        parameters=[
            OpenApiParameter(name='shop_slug', type=OpenApiTypes.STR, location=OpenApiParameter.PATH, description='Shop slug')
        ],
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'image': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Image file (JPEG or PNG, max 5MB)'
                    },
                    'alt_text': {
                        'type': 'string',
                        'description': 'Alt text for the image'
                    },
                    'shop': {
                        'type': 'string',
                        'format': 'uuid',
                        'description': 'Shop UUID'
                    }
                },
                'required': ['image', 'shop']
            }
        },
        responses={201: ShopMediaSerializer, 400: None, 403: None}
    )
    def post(self, request, shop_slug):
        user = request.user
        logger.info(f"POST /media/{shop_slug}/create/ - Media creation request from user {user.id}")
        data = request.data.copy()  
        data['user'] = str(user.id)
        shop = get_object_or_404(Shop, slug=shop_slug, is_active=True, status=Shop.APPROVED)
        if str(shop.user) != str(user.id):
            logger.warning(f"POST /media/{shop_slug}/create/ - Permission denied for user {user.id}")
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ShopMediaSerializer(
            data=data, context={
            'request': request,
            'shop': shop
        })
        if serializer.is_valid():
            media = serializer.save()
            logger.info(f"POST /media/{shop_slug}/create/ - Media {media.id} created successfully for shop {shop.id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        logger.warning(f"POST /media/{shop_slug}/create/ - Validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteShopMediaAPIView(APIView):
    """Allows the owner to delete their shop media."""
    http_method_names = ['delete']
    permission_classes = [IsAuthenticated]
    authentication_classes = [GatewayHeaderAuthentication]
    
    @extend_schema(
        operation_id='media_delete',
        summary='Delete shop media',
        description='Delete a media file. Only the shop owner can delete media.',
        tags=['ShopMedia'],
        parameters=[
            OpenApiParameter(name='media_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='Media ID')
        ],
        responses={204: None, 403: None}
    )
    def delete(self, request, media_id):
        user = request.user
        logger.info(f"DELETE /media/{media_id}/delete/ - Delete request from user {user.id}")
        shop_media = get_object_or_404(ShopMedia, id=media_id)
        if str(shop_media.shop.user) != str(request.user.id):
            logger.warning(f"DELETE /media/{media_id}/delete/ - Permission denied for user {user.id}")
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
        
        shop_media.delete()
        logger.info(f"DELETE /media/{media_id}/delete/ - Media {shop_media.id} deleted successfully")
        return Response(status=status.HTTP_204_NO_CONTENT)


# ShopScoialMedia Views
class ShopSocialMediaListByShopAPIView(APIView):
    """Returns a list of branches for a given shop."""
    http_method_names = ['get']

    def get(self, request, shop_slug):
        shop = get_object_or_404(Shop, slug=shop_slug, is_active=True, status=Shop.APPROVED)
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

    @extend_schema(
        operation_id='social_media_create',
        summary='Create shop social media',
        description='Add social media links for a shop. Only the shop owner can add social media.',
        tags=['ShopSocialMedia'],
        parameters=[
            OpenApiParameter(name='shop_slug', type=OpenApiTypes.STR, location=OpenApiParameter.PATH, description='Shop slug')
        ],
        request=ShopSocialMediaSerializer,
        responses={201: ShopSocialMediaSerializer, 400: None, 403: None}
    )
    def post(self, request, shop_slug):
        user = request.user
        logger.info(f"POST /social-media/{shop_slug}/create/ - Social media creation request from user {user.id}")
        data = request.data.copy()  
        data['user'] = str(user.id)
        shop = get_object_or_404(Shop, slug=shop_slug, is_active=True, status=Shop.APPROVED)
        if str(shop.user) != str(user.id):
            logger.warning(f"POST /social-media/{shop_slug}/create/ - Permission denied for user {user.id}")
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ShopSocialMediaSerializer(
            data=data, context={
                'request': request,
                'shop': shop
        })
        if serializer.is_valid():
            social_media = serializer.save()
            logger.info(f"POST /social-media/{shop_slug}/create/ - Social media {social_media.id} created successfully for shop {shop.id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        logger.warning(f"POST /social-media/{shop_slug}/create/ - Validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShopSocialMediaManagementAPIView(APIView):
    """Allows the owner to update or delete their shop social media."""
    http_method_names = ['patch', 'delete']
    permission_classes = [IsAuthenticated]
    authentication_classes = [GatewayHeaderAuthentication]

    @extend_schema(
        operation_id='social_media_update',
        summary='Update shop social media',
        description='Update social media information. Only the shop owner can update.',
        tags=['ShopSocialMedia'],
        parameters=[
            OpenApiParameter(name='social_media_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='Social media ID')
        ],
        request=ShopSocialMediaSerializer,
        responses={200: ShopSocialMediaSerializer, 400: None, 403: None}
    )
    def patch(self, request, social_media_id):
        user = request.user
        logger.info(f"PATCH /social-media/{social_media_id}/management/ - Update request from user {user.id}")
        data = request.data
        social_media = get_object_or_404(ShopSocialMedia, id=social_media_id)
        if str(social_media.shop.user) != str(request.user.id):
            logger.warning(f"PATCH /social-media/{social_media_id}/management/ - Permission denied for user {user.id}")
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ShopSocialMediaSerializer(social_media, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"PATCH /social-media/{social_media_id}/management/ - Social media {social_media.id} updated successfully")
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        logger.warning(f"PATCH /social-media/{social_media_id}/management/ - Validation failed: {serializer.errors}")
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        operation_id='social_media_delete',
        summary='Delete shop social media',
        description='Delete a social media link. Only the shop owner can delete.',
        tags=['ShopSocialMedia'],
        parameters=[
            OpenApiParameter(name='social_media_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='Social media ID')
        ],
        responses={204: None, 403: None}
    )
    def delete(self, request, social_media_id):
        user = request.user
        logger.info(f"DELETE /social-media/{social_media_id}/management/ - Delete request from user {user.id}")
        social_media = get_object_or_404(ShopSocialMedia, id=social_media_id)
        if str(social_media.shop.user) != str(request.user.id):
            logger.warning(f"DELETE /social-media/{social_media_id}/management/ - Permission denied for user {user.id}")
            return Response({'error': 'You do not have permission'}, status=status.HTTP_403_FORBIDDEN)
        
        social_media.delete()
        logger.info(f"DELETE /social-media/{social_media_id}/management/ - Social media {social_media.id} deleted successfully")
        return Response(status=status.HTTP_204_NO_CONTENT)


# ShopOrderItem Views
class ShopOrderItemListAPIView(APIView):
    """List all order items for a specific shop. Only shop owner can view."""
    http_method_names = ['get']
    permission_classes = [IsAuthenticated]
    authentication_classes = [GatewayHeaderAuthentication]
    pagination_class = CustomPagination

    def get(self, request, shop_slug):
        shop = get_object_or_404(Shop, slug=shop_slug, is_active=True)
        pagination = self.pagination_class()
        order_items = ShopOrderItem.objects.filter(shop=shop)
        paginated_items = pagination.paginate_queryset(order_items, request)

        if paginated_items is not None:
            serializer = ShopOrderItemSerializer(paginated_items, many=True)
            return pagination.get_paginated_response(serializer.data)
        
        serializer = ShopOrderItemSerializer(order_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ShopOrderItemDetailAPIView(APIView):
    """Get details of a specific order item. Only shop owner can view."""
    http_method_names = ['get']
    permission_classes = [IsAuthenticated]
    authentication_classes = [GatewayHeaderAuthentication]

    def get(self, request, order_item_id):
        order_item = get_object_or_404(ShopOrderItem, id=order_item_id)
        serializer = ShopOrderItemSerializer(order_item)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ShopOrderItemStatusUpdateAPIView(APIView):
    """Update the status of an order item. Only shop owner can update."""
    http_method_names = ['patch']
    permission_classes = [IsAuthenticated]
    authentication_classes = [GatewayHeaderAuthentication]

    @extend_schema(
        operation_id='shop_order_item_status_update',
        summary='Update order item status',
        description='Update the status of an order item. Only the shop owner can update.',
        tags=['ShopOrderItem'],
        parameters=[
            OpenApiParameter(name='order_item_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='Order item ID')
        ],
        request=ShopOrderItemStatusUpdateSerializer,
        responses={200: ShopOrderItemSerializer, 400: None, 403: None, 404: None}
    )
    def patch(self, request, order_item_id):
        user = request.user
        order_item = get_object_or_404(ShopOrderItem, id=order_item_id)
        serializer = ShopOrderItemStatusUpdateSerializer(order_item, data=request.data, partial=True)
        if serializer.is_valid():
            new_status = serializer.validated_data.get('status')
            
            # Update status in order-service (source of truth)
            # Shop-service will receive status update via RabbitMQ event
            order_service_response = order_client.update_order_item_status(
                order_item_id=order_item_id,
                status=new_status,
                shop_owner_user_id=str(user.id)  
            )
            
            if order_service_response is None:
                logger.error(f"Failed to update order item {order_item_id} status in order service")
                return Response(
                    {'error': 'Failed to update order item status in order service'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Update local status from order-service response (source of truth)
            updated_status = order_service_response.get('status')
            if updated_status is not None:
                order_item.status = updated_status
                order_item.save(update_fields=['status'])
            
            full_serializer = ShopOrderItemSerializer(order_item)
            return Response(full_serializer.data, status=status.HTTP_200_OK)
        
        logger.warning(f"PATCH /order-items/{order_item_id}/status/ - Validation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        