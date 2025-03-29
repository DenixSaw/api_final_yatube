from django.http import Http404
from rest_framework import viewsets, status, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter
from api.serializers import (PostSerializer, FollowSerializer,
                             CommentSerializer, GroupSerializer)
from posts.models import Post, Follow, Group, Comment
from rest_framework.response import Response


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = LimitOffsetPagination


class PostViewSet(BaseViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.author != request.user:
            return Response(
                {"detail": "У вас недостаточно"
                           " прав для выполнения "
                           "данного"
                           " действия."}, status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return Response(
                {"detail": 'У вас недостаточно'
                           ' прав для выполнения '
                           'данного '
                           'действия.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data, status=status.HTTP_200_OK)


class CommentViewSet(BaseViewSet):
    serializer_class = CommentSerializer

    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        return Comment.objects.filter(post=post_id)

    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, pk=post_id)
        serializer.save(post=post, author=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        comment_id = self.kwargs.get('pk')
        try:
            comment = Comment.objects.get(id=comment_id)
            serializer = CommentSerializer(comment)
            return Response(serializer.data)
        except Comment.DoesNotExist:
            return Response({"detail": "Страница не найдена."},
                            status=status.HTTP_404_NOT_FOUND)

    def update(self, request, *args, **kwargs):
        try:
            comment = Comment.objects.get(id=kwargs.get('pk'))
            serializer = self.get_serializer(comment,
                                             data=request.data,
                                             partial=False)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data,
                            status=status.HTTP_200_OK)
        except Comment.DoesNotExist:
            return Response({"detail": "Ком"
                                       "мен"
                                       "тар"
                                       "ий не на"
                                       "йд"
                                       "ен"}, status=status.HTTP_404_NOT_FOUND)

    def partial_update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()

            if instance.author != request.user:
                return Response(
                    {"detail": "У вас"
                               " недостаточно"
                               " прав для редактирования ком"
                               "ментария"}, status=status.HTTP_403_FORBIDDEN)

            serializer = self.get_serializer(
                instance,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Http404:
            return Response({"detail": "Коммент"
                                       "арий не н"
                                       "айд"
                                       "ен"}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance.author != request.user:
                return Response({"detail": "У вас недостаточно п"
                                           "рав для выпол"
                                           "нения данного де"
                                           "йств"
                                           "ия"
                                           "."},
                                status=status.HTTP_403_FORBIDDEN)
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Http404:
            return Response({"detail": "Комме"
                                       "нтарий не найден"
                                       ""}, status=status.HTTP_404_NOT_FOUND)


class FollowViewSet(viewsets.ModelViewSet):
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ['following__username']

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Response({"detail": "У вас н"
                                       "едостаточно пр"
                                       "ав для выполнения дан"
                                       "ного действия"
                                       "."},
                            status=status.HTTP_401_UNAUTHORIZED)

        queryset = Follow.objects.filter(user=self.request.user)

        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(
                following__username__icontains=search_query
            )
        return queryset

    def perform_create(self, serializer):
        following_user = serializer.validated_data['following']

        if following_user == self.request.user:
            raise ValidationError(
                {"detail": "Нельзя подписаться на самого себя"})

        if Follow.objects.filter(
                user=self.request.user,
                following=following_user
        ).exists():
            raise ValidationError(
                {"detail": "Вы уже подписаны на этого пользователя"})

        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class GroupViewSet(BaseViewSet):
    serializer_class = GroupSerializer
    queryset = Group.objects.all()
    http_method_names = ['get', 'head', 'options']
