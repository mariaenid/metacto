from ..application.ports import CommentServices
from .repositories import DjangoCommentRepository


def build_comment_services() -> CommentServices:
    return CommentServices(comments=DjangoCommentRepository())
