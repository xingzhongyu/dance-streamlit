# app.py
import streamlit as st
import os
from PIL import Image
import math
from io import BytesIO

# 设置页面配置
st.set_page_config(
    page_title="UMAP 图集展示",
    layout="wide",
)

# 页面标题
st.title("UMAP 图集展示")

# 图像根目录
UMAP_ROOT_DIR = 'single_dataset_umap_imgs'
if not os.path.exists(UMAP_ROOT_DIR):
    st.error(f"图像根目录 `{UMAP_ROOT_DIR}` 不存在。请确保UMAP图像存放在该目录下。")
    st.stop()

# 支持的图像扩展名
SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif')

@st.cache_data
def get_all_images(root_dir):
    """
    递归地获取所有图像文件的相对路径。
    """
    image_list = []
    for dirpath, _, filenames in os.walk(root_dir):
        for file in filenames:
            if file.lower().endswith(SUPPORTED_EXTENSIONS):
                # 获取相对于根目录的路径
                rel_dir = os.path.relpath(dirpath, root_dir)
                rel_path = os.path.join(rel_dir, file)
                image_list.append(rel_path)
    return sorted(image_list)

all_images = get_all_images(UMAP_ROOT_DIR)

# 侧边栏 - 多级过滤
st.sidebar.header("过滤选项")

# 辅助函数：分解路径层级
def get_path_levels(path, levels=4):
    parts = path.split(os.sep)
    return parts[:levels]

# 动态获取所有层级的独特选项
def get_unique_options(images, level):
    options = set()
    for img in images:
        parts = img.split(os.sep)
        if len(parts) > level:
            options.add(parts[level])
    return sorted(options)

# 初始化过滤器
selected_filters = []

for level in range(4):  # 0到3代表4级目录
    options = get_unique_options(all_images, level)
    if options:
        selected = st.sidebar.selectbox(
            f"选择第 {level + 1} 级目录",
            ["所有"] + options,
            key=f"filter_level_{level}"
        )
        selected_filters.append(selected)

# 应用过滤器
filtered_images = all_images.copy()
for level, selected in enumerate(selected_filters):
    if selected != "所有":
        filtered_images = [
            img for img in filtered_images
            if get_path_levels(img, levels=level + 1)[level] == selected
        ]

# 搜索功能
search_query = st.sidebar.text_input("搜索图像名称").strip().lower()
if search_query:
    keywords = search_query.split()
    for keyword in keywords:
        filtered_images = [img for img in filtered_images if keyword in os.path.basename(img).lower()]

total_images = len(filtered_images)
if total_images == 0:
    st.warning("没有找到符合条件的图像。")
    st.stop()

# 分页参数
images_per_page = 12
total_pages = math.ceil(total_images / images_per_page)

# 当前页面选择器
page_number = st.sidebar.number_input("页码", min_value=1, max_value=total_pages, value=1, step=1)

# 计算当前页显示的图像
start_idx = (page_number - 1) * images_per_page
end_idx = start_idx + images_per_page
current_images = filtered_images[start_idx:end_idx]

# 显示图像
cols = st.columns(4)
for idx, img_path in enumerate(current_images):
    with cols[idx % 4]:
        full_path = os.path.join(UMAP_ROOT_DIR, img_path)
        try:
            image = Image.open(full_path)
            # 使用相对路径作为唯一标识
            caption = img_path.replace(os.sep, " / ")
            st.image(image, caption=caption, use_container_width=True)
            
            # 添加下载按钮
            buffer = BytesIO()
            image.save(buffer, format=image.format if image.format else "PNG")
            buffer.seek(0)
            download_label = f"下载 - {os.path.basename(img_path)}"
            # 为避免名称冲突，使用相对路径中的下划线替换分隔符
            download_name = img_path.replace(os.sep, "_")
            st.download_button(
                label=download_label,
                data=buffer,
                file_name=download_name,
                mime=f"image/{image.format.lower()}" if image.format else "image/png"
            )
        except Exception as e:
            st.error(f"无法加载图像 `{img_path}`: {e}")

# 显示页码信息
st.write(f"显示 {start_idx + 1} - {min(end_idx, total_images)} 张 / 共 {total_images} 张图像")