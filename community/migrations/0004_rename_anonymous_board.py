"""
익명게시판 이름을 '멘토의 취업비밀' 로 바꿉니다.

게시판 이름은 board 표에 들어 있는 데이터라 모델을 고쳐도 바뀌지 않습니다.
이미 운영 중인 DB 도 함께 바꾸려고 데이터 마이그레이션으로 처리합니다.
글·댓글·권한은 board_id 로 연결되어 있으므로 이름만 바꿔도 그대로 붙어 있습니다.
"""

from django.db import migrations

OLD_NAME = "익명게시판"
NEW_NAME = "멘토의 취업비밀"


def rename(apps, schema_editor):
    Board = apps.get_model("community", "Board")
    Board.objects.filter(board_name=OLD_NAME).update(board_name=NEW_NAME)


def rollback(apps, schema_editor):
    Board = apps.get_model("community", "Board")
    Board.objects.filter(board_name=NEW_NAME).update(board_name=OLD_NAME)


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0003_board_is_anonymous_post_accepted_answer_and_more'),
    ]

    operations = [
        migrations.RunPython(rename, rollback),
    ]
