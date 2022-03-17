import json
from datetime import datetime

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from feed.services.bookmark_service import do_bookmark, undo_bookmark
from feed.services.comment_service import (
    create_an_comment,
    delete_an_comment,
    get_comment_list,
    update_an_comment,
)
from feed.services.feed_service import (
    create_an_feed,
    delete_an_feed,
    get_an_feed,
    get_feed_list,
    get_popular_feed_list,
    update_an_feed,
    upload_feed_image,
)
from feed.services.like_service import do_like, undo_like
from greendoor.utils import allowed_file, get_file_extension

URL_LOGIN = "/login/"  # TODO login url 작업 완료 되면 수정
URL_S3 = "https://nmdbucket.s3.amazonaws.com/"


def community_view(request: HttpRequest) -> HttpResponse:
    # 요청하는 방식이 get 방식인지 확인
    if request.method == "GET":
        # 로그인이 되어있다면
        if request.user.is_authenticated:
            user_id = request.user.id
        # 로그인이 되어있지 않다면
        else:
            # 없는 사용자 id
            user_id = 0

        # 클라이언트에서 전해준 page 값을 저장 (default : none -> 1, "" -> 1)
        page = int(request.GET.get("page", 1) or 1)
        limit = 40
        offset = limit * (page - 1)

        # 피드 리스트 가져오기
        all_feed = get_feed_list(user_id, offset, limit)

        # 첫 페이지라면
        if offset == 0:
            popular_feeds = get_popular_feed_list(user_id, offset, 20)
            return render(request, "feed_test_html/index.html", {"all_feed": all_feed, "popular_feeds": popular_feeds})

        return render(request, "feed_test_html/index.html", {"all_feed": all_feed})

    # 다른 방식으로 요청이 오면 index 페이지로 리다이렉트
    else:
        return redirect("feed:community")


# 피드를 보여주는 함수
def feed_view(request: HttpRequest, feed_id: int) -> HttpResponse:
    # 요청 방식이 get 방식인지 확인
    if request.method == "GET":
        # 로그인이 되어있다면
        if request.user.is_authenticated:
            # 로그인된 사용자 id
            user_id = request.user.id
        # 로그인이 되어있지 않다면
        else:
            # 없는 사용자 id
            user_id = 0
        # 피드 가져오기
        feed = get_an_feed(user_id, feed_id)
        comments = get_comment_list(feed.id, 0, 10)

        return render(request, "feed_test_html/feed.html", {"feed": feed, "comments": comments})

    # 다른 방식으로 요청이 오면 index 페이지로 리다이렉트
    else:
        return redirect("feed:community")


# 피드 작성 페이지 뷰, api
def create_feed_view(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect(URL_LOGIN)
    # get 방식일 때
    if request.method == "GET":
        return render(request, "feed_test_html/create_feed.html")
    # post 방식일 때
    elif request.method == "POST":
        # title, content 정보 가져오기
        title = request.POST.get("feed_title", "")
        content = request.POST.get("feed_content", "")
        # title 값이 공백이면
        if title == "":
            return render(request, "feed_test_html/create_feed.html", {"error": "피드에 제목은 필수! :)"})

        # request에 파일 정보가 있으면
        if "feed_img_file" in request.FILES:
            # 사용자 정보 가져오기
            user = request.user
            # request에 있는 file 정보 가져오기
            img_file = request.FILES["feed_img_file"]
            # 파일의 확장자 검사 및 이름을 현재 시간으로 지정
            if img_file and allowed_file(img_file.name):
                ext = get_file_extension(img_file.name)
                filename = f"file_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                img_file.name = filename
                # 이미지 업로드
                img = upload_feed_image(img_file)
                img_url = URL_S3 + img.img.name
                # print(img.img.path)
                # 모든 예외처리를 통과하면
                # 피드 저장 후 저장된 피드의 페이지로 이동
                feed = create_an_feed(user_id=user.id, title=title, image=img_url, content=content)
                return redirect("feed:feed", feed.id)
            # 허용되지 않은 확장자인 경우
            else:
                return render(
                    request, "feed_test_html/create_feed.html", {"error": "jpg, jpeg, gif, png 확장자를 사용해주세요 :)"}
                )
        # request에 파일 정보가 없으면
        else:
            return render(request, "feed_test_html/create_feed.html", {"error": "피드에 사진은 필수! :)"})
    # 그 외 방식일 때
    else:
        return redirect("feed:community")


# 피드 업데이트 함수
def update_feed_view(request: HttpRequest, feed_id: int) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect(URL_LOGIN)
    user_id = request.user.id

    # GET 방식일 때
    if request.method == "GET":
        feed = get_an_feed(user_id=user_id, feed_id=feed_id)
        return render(request, "feed_test_html/update_feed.html", {"feed": feed})

    # POST 방식일 때
    elif request.method == "POST":
        # title, content 정보 가져오기
        title = request.POST.get("feed_title", "")
        content = request.POST.get("feed_content", "")
        # title 값이 공백이면
        if title == "":
            return render(request, "feed_test_html/create_feed.html", {"error": "피드에 제목은 필수! :)"})

        # request에 파일 정보가 있으면
        if "feed_img_file" in request.FILES:
            # 사용자 정보 가져오기
            user = request.user
            # request에 있는 file 정보 가져오기
            img_file = request.FILES["feed_img_file"]
            # 파일의 확장자 검사 및 이름을 현재 시간으로 지정
            if img_file and allowed_file(img_file.name):
                ext = get_file_extension(img_file.name)
                filename = f"file_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                img_file.name = filename
                # 이미지 업로드
                img = upload_feed_image(img_file)
                img_url = URL_S3 + img.img.name

                # 모든 예외처리를 통과하면
                # 피드 업데이트 후 저장된 피드의 페이지로 이동
                update_an_feed(user_id=user.id, feed_id=feed_id, title=title, image=img_url, content=content)
                return redirect("feed:feed", feed_id)
                # 허용되지 않은 확장자인 경우
            else:
                return render(
                    request, "feed_test_html/create_feed.html", {"error": "jpg, jpeg, gif, png 확장자를 사용해주세요 :)"}
                )
        # request에 파일 정보가 없으면
        else:
            return render(request, "feed_test_html/create_feed.html", {"error": "피드에 사진은 필수! :)"})

    # POST와 GET 이외의 요청일 때
    else:
        return redirect("feed:community")


# 피드 삭제 api
def api_delete_feed(request: HttpRequest, feed_id: int) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect(URL_LOGIN)
    user_id = request.user.id
    # 댓글 삭제 서비스 함수 실행
    delete_an_feed(feed_id=feed_id, user_id=user_id)
    return redirect("feed:community")


# 좋아요 api
@require_POST
def api_like(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect(URL_LOGIN)

    # 사용자 정보 가져오기
    user = request.user
    feed_id = request.POST["feed_id"]
    feed = get_an_feed(user_id=user.id, feed_id=feed_id)
    feed_like_count = feed.like_count

    # 좋아요를 한 상태이면 좋아요 취소
    if feed.my_likes:
        undo_like(user_id=user.id, feed_id=feed_id)
        msg = "좋아요 취소"
        feed_like_count -= 1
    # 좋아요를 안한 상태이면 좋아요
    else:
        do_like(user_id=user.id, feed_id=feed_id)
        msg = "좋아요"
        feed_like_count += 1

    context = {"msg": msg, "like_count": feed_like_count}
    return HttpResponse(json.dumps(context), content_type="application/json")


# 북마크 api
@require_POST
def api_bookmark(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect(URL_LOGIN)

    # 사용자 정보 가져오기
    user = request.user
    feed_id = request.POST["feed_id"]
    feed = get_an_feed(user_id=user.id, feed_id=feed_id)

    # 북마크를 한 상태이면 북마크 취소
    if feed.my_bookmark:
        undo_bookmark(user_id=user.id, feed_id=feed_id)
        msg = "북마크 취소"
    # 북마크를 안한 상태이면 북마크
    else:
        do_bookmark(user_id=user.id, feed_id=feed_id)
        msg = "북마크"

    context = {"msg": msg}
    return HttpResponse(json.dumps(context), content_type="application/json")


# 댓글 작성 api
def api_create_comment(request: HttpRequest, feed_id: int) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect(URL_LOGIN)

    if request.method == "POST":
        # 사용자 정보 가져오기
        user = request.user
        # post 형식의 form 태그에서 content를 가져옴
        content = request.POST.get("comment_content", "")
        # 댓글 생성 서비스 함수 실행
        create_an_comment(user_id=user.id, feed_id=feed_id, content=content)
        return redirect("feed:feed", feed_id)
    else:
        return redirect("feed:community")


# 댓글 수정
@require_POST
def api_update_comment(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect(URL_LOGIN)

    user_id = request.user.id
    comment_id = request.POST["comment_id"]
    content = request.POST["content"]
    update_an_comment(user_id=user_id, comment_id=comment_id, content=content)
    context = {"msg": "success"}
    return HttpResponse(json.dumps(context), content_type="application/json")


# 댓글 삭제 api
def api_delete_comment(request: HttpRequest, feed_id: int, comment_id: int) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect(URL_LOGIN)

    user_id = request.user.id
    # 댓글 삭제 서비스 함수 실행
    delete_an_comment(comment_id=comment_id, user_id=user_id)
    return redirect("feed:feed", feed_id)
