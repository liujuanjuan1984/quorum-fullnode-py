import base64
import datetime
import io
import logging
import os
import uuid
import zipfile

import filetype
from PIL import Image
from pygifsicle import gifsicle

from quorum_fullnode_py.exceptions import ParamTypeError, ParamValueError

logger = logging.getLogger(__name__)


# 将一张或多张图片处理成 RUM 支持的图片对象列表, 要求总大小小于 200kb，此为链端限定
IMAGE_MAX_SIZE_KB = 200  # 200 kb 每条trx中所包含的图片总大小限制为 200
# 单条 trx 最多4 张图片；此为 rum app 客户端限定：第三方 app 调整该限定
IMAGE_MAX_NUM = 4
CHUNK_SIZE = 150 * 1024  # 150 kb，文件切割为多条trxs时，每条trx所包含的文件字节流上限


def _filename_init_from_bytes(file_bytes):
    extension = filetype.guess(file_bytes).extension
    name = f"{uuid.uuid4()}-{datetime.date.today()}"
    return ".".join([name, extension])


def _filename_init(path_bytes_string):
    file_bytes, is_file = _get_filebytes(path_bytes_string)
    if is_file:
        file_name = os.path.basename(path_bytes_string).encode().decode("utf-8")
    else:
        file_name = _filename_init_from_bytes(file_bytes)
    return file_name


def _zip_image_bytes(img_bytes, kb=IMAGE_MAX_SIZE_KB):
    """zip image bytes and return bytes; default changed to .jpeg"""

    kb = kb or IMAGE_MAX_SIZE_KB
    guess_extension = filetype.guess(img_bytes).extension

    with io.BytesIO(img_bytes) as im:
        size = len(im.getvalue()) // 1024
        if size < kb:
            return img_bytes
        while size >= kb:
            img = Image.open(im)
            x, y = img.size
            out = img.resize((int(x * 0.95), int(y * 0.95)), Image.ANTIALIAS)
            im.close()
            im = io.BytesIO()
            try:
                out.save(im, "jpeg")
            except Exception as err:
                logger.debug(err)
                out.save(im, guess_extension)
            size = len(im.getvalue()) // 1024
        return im.getvalue()


def check_file(file_path):
    if not os.path.exists(file_path):
        raise ParamValueError(f"{file_path} file is not exists.")

    if not os.path.isfile(file_path):
        raise ParamValueError(f"{file_path} is not a file.")


def read_file_to_bytes(file_path):
    check_file(file_path)
    with open(file_path, "rb") as f:
        bytes_data = f.read()
    return bytes_data


def zip_file(file_path, to_zipfile=None, mode="w"):
    check_file(file_path)
    to_zipfile = to_zipfile or file_path + "_.zip"
    with zipfile.ZipFile(to_zipfile, mode, zipfile.ZIP_DEFLATED) as zf:
        zf.write(file_path, arcname=os.path.basename(file_path))
    return to_zipfile


def zip_gif(gif, kb=IMAGE_MAX_SIZE_KB, cover=False):
    """压缩动图(gif)到指定大小(kb)以下

    gif: gif 格式动图本地路径
    kb: 指定压缩大小, 默认 200kb
    cover: 是否覆盖原图, 默认不覆盖

    返回压缩后图片字节. 该方法需要安装 gifsicle 软件和 pygifsicle 模块
    """
    kb = kb or IMAGE_MAX_SIZE_KB
    size = os.path.getsize(gif) / 1024
    if size < kb:
        return read_file_to_bytes(gif)

    destination = None
    if not cover:
        destination = f"{os.path.splitext(gif)[0]}-zip.gif"

    n = 0.9
    while size >= kb:
        gifsicle(
            gif,
            destination=destination,
            optimize=True,
            options=["--lossy=80", "--scale", str(n)],
        )
        if not cover:
            gif = destination
        size = os.path.getsize(gif) / 1024
        n -= 0.05

    return read_file_to_bytes(gif)


def _zip_image(path_bytes_string, kb=IMAGE_MAX_SIZE_KB):
    file_bytes, is_file = _get_filebytes(path_bytes_string)

    try:
        if filetype.guess(file_bytes).extension == "gif" and is_file:
            img_bytes = zip_gif(path_bytes_string, kb=kb, cover=False)
        else:
            img_bytes = _zip_image_bytes(file_bytes, kb=kb)
    except Exception as e:
        logger.warning("zip_image %s", e)
    return img_bytes


def _group_icon(icon):
    """icon: one image as file path, or bytes, or bytes-string."""

    img_bytes = _zip_image(icon)
    icon = "".join(
        [
            "data:",
            filetype.guess(img_bytes).mime,
            ";base64,",
            base64.b64encode(img_bytes).decode("utf-8"),
        ]
    )
    return icon


def _get_filebytes(path_bytes_string):
    _size = len(path_bytes_string)
    is_file = False
    if isinstance(path_bytes_string, str):
        if os.path.exists(path_bytes_string):
            file_bytes = read_file_to_bytes(path_bytes_string)
            is_file = True
        else:
            file_bytes = base64.b64decode(path_bytes_string)
    elif isinstance(path_bytes_string, bytes):
        file_bytes = path_bytes_string
    else:
        raise ParamTypeError(
            f"not support for type: {type(path_bytes_string)} and length: {_size}"
        )
    return file_bytes, is_file


def _pack_images(images):
    kb = int(IMAGE_MAX_SIZE_KB // min(len(images), IMAGE_MAX_NUM))
    imgs = []
    for path_bytes_string in images[:IMAGE_MAX_NUM]:
        if isinstance(path_bytes_string, dict):
            icontent = path_bytes_string.get("content")
            if not icontent:
                err = (
                    f"image  type: {type(path_bytes_string)} ,content got null "
                )
                raise ParamValueError(err)
            _bytes, _ = _get_filebytes(icontent)
            iname = path_bytes_string.get("name", _filename_init(_bytes))
            imediaType = path_bytes_string.get(
                "mediaType", filetype.guess(_bytes).mime
            )
        else:
            iname = _filename_init(path_bytes_string)
            _bytes = _zip_image(path_bytes_string, kb)
            imediaType = filetype.guess(_bytes).mime
            icontent = base64.b64encode(_bytes).decode("utf-8")

        # if isinstance(icontent, str):
        #    icontent = base64.b64decode(icontent)
        imgs.append(
            {"name": iname, "mediaType": imediaType, "content": icontent}
        )

    return imgs


def _pack_content(content: str, images: list, name: str, post_id: str):
    content = content or ""
    images = images or []
    if len(content) < 1:
        raise ParamValueError("content is empty")
    if not (content or images):
        raise ParamValueError("content and images are empty")

    content_obj = {"type": "Note"}
    if content:
        content_obj["content"] = content
    if images:
        content_obj["image"] = _pack_images(images)
    if name:
        content_obj["name"] = name
    content_obj["id"] = post_id or str(uuid.uuid4())
    return content_obj


class FeedData:
    """适用于 feed 的 trx 数据结构"""

    @classmethod
    def new_post(
        cls, content: str, images: list, post_id: str = None, name: str = None
    ):
        return {
            "type": "Create",
            "object": _pack_content(content, images, name, post_id),
        }

    @classmethod
    def del_post(cls, post_id):
        return {"type": "Delete", "object": {"type": "Note", "id": post_id}}

    @classmethod
    def edit_post(
        cls, content: str, images: list, post_id: str = None, name: str = None
    ):
        content_obj = _pack_content(content, images, name, post_id)
        del content_obj["id"]
        return {
            "type": "Update",
            "object": {
                "type": "Note",
                "id": post_id,
            },
            "result": content_obj,
        }

    @classmethod
    def reply(
        cls,
        content: str,
        images: list,
        reply_id: str,
        post_id: str = None,
        name: str = None,
    ):
        content_obj = _pack_content(content, images, name, post_id)
        content_obj["inreplyto"] = {"type": "Note", "id": reply_id}
        return {"type": "Create", "object": content_obj}

    @classmethod
    def like(cls, post_id: str):
        return {"type": "Like", "object": {"type": "Note", "id": post_id}}

    @classmethod
    def undo_like(cls, post_id: str):
        return {
            "type": "Undo",
            "object": {
                "type": "Like",
                "object": {"type": "Note", "id": post_id},
            },
        }

    @classmethod
    def dislike(cls, post_id: str):
        return {"type": "Dislike", "object": {"type": "Note", "id": post_id}}

    @classmethod
    def undo_dislike(cls, post_id: str):
        return {
            "type": "Undo",
            "object": {
                "type": "Dislike",
                "object": {"type": "Note", "id": post_id},
            },
        }

    @classmethod
    def profile(cls, name: str, avatar: str, addr: str):
        """update profile of user"""
        if not (name or avatar):
            raise ParamValueError("name and avatar are empty")
        profile_obj = {
            "type": "Profile",
            "describes": {"type": "Person", "id": addr},
        }
        if name:
            profile_obj["name"] = name
        if avatar:
            profile_obj["image"] = _pack_images([avatar])
        return {"type": "Create", "object": profile_obj}

    @classmethod
    def follow_user(cls, addr: str):
        return {
            "type": "Follow",
            "object": {
                "type": "Person",
                "id": addr,
            },
        }

    @classmethod
    def unfollow_user(cls, addr: str):
        return {
            "type": "Undo",
            "object": {
                "type": "Follow",
                "object": {"type": "Person", "id": addr},
            },
        }

    @classmethod
    def block_user(cls, addr: str):
        return {
            "type": "Block",
            "object": {"type": "Person", "id": addr},
        }

    @classmethod
    def unblock_user(cls, addr: str):
        return {
            "type": "Undo",
            "object": {
                "type": "Block",
                "object": {"type": "Person", "id": addr},
            },
        }

    @classmethod
    def group_icon(cls, icon: str):
        """init group icon as appconfig"""
        return {
            "name": "group_icon",
            "_type": "string",
            "value": _group_icon(icon),
            "action": "add",
            "memo": "init group icon",
        }

    @classmethod
    def group_desc(cls, desc: str):
        """init group description as appconfig"""
        return {
            "name": "group_desc",
            "_type": "string",
            "value": desc,
            "action": "add",
            "memo": "init group desc",
        }

    @classmethod
    def group_announcement(cls, announcement: str):
        """init group announcement as appconfig"""
        return {
            "name": "group_announcement",
            "_type": "string",
            "value": announcement,
            "action": "add",
            "memo": "init group announcement",
        }

    @classmethod
    def group_default_permission(cls, default_permission: str):
        """init group default permission as appconfig
        default_permission: WRITE or READ"""
        if default_permission.upper() not in ["WRITE", "READ"]:
            raise ParamValueError(
                "default_permission must be one of these: WRITE,READ"
            )
        return {
            "name": "group_default_permission",
            "_type": "string",
            "value": default_permission.upper(),
            "action": "add",
            "memo": "init group default permission",
        }
