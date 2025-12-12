from fastapi import HTTPException
from src.app.models.v1 import Comment

class CommentPermission:
    def __init__(self, db, user_id):
        self.db = db
        self.user_id = user_id

    def check_comment_owner(self, comment_id):
        comment = (
            self.db.query(Comment)
            .filter(Comment.comment_id == comment_id)
            .first()
        )

        if not comment:
            raise HTTPException(404, "Comment not found")

        if str(comment.user_id) != str(self.user_id):
            raise HTTPException(403, "Not authorized to modify this comment")