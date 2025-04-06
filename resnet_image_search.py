#!/usr/bin/env python3
"""
File: resnet_image_search.py
Mô tả: Tìm kiếm ảnh theo nội dung trực tiếp (CBIR) sử dụng mô hình ResNet50 pretrained.
Sử dụng:
    python resnet_image_search.py --query <query_image_path> --images_dir <path_to_candidate_images> --top <number_of_results>
Ví dụ:
    python resnet_image_search.py --query query.jpg --images_dir ./flickr30k_images --top 5
"""

import argparse
import os
import torch
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image

def load_image(image_path, transform):
    image = Image.open(image_path).convert('RGB')
    return transform(image)

def extract_feature(image_tensor, model, device):
    image_tensor = image_tensor.unsqueeze(0).to(device)
    with torch.no_grad():
        feature = model(image_tensor)
    # feature có shape [1, 2048, 1, 1] -> flatten thành vector 1 chiều
    feature = feature.squeeze().view(-1)
    return feature

def main():
    parser = argparse.ArgumentParser(description="Content-based Image Retrieval using ResNet50")
    parser.add_argument("--query", type=str, required=True, help="Đường dẫn đến ảnh query")
    parser.add_argument("--images_dir", type=str, required=True, help="Thư mục chứa ảnh candidate")
    parser.add_argument("--top", type=int, default=5, help="Số lượng kết quả hiển thị")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Định nghĩa transform cho ảnh (theo chuẩn của ResNet)
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])

    # Tải mô hình ResNet50 pretrained và loại bỏ lớp cuối cùng (fully connected)
    resnet = models.resnet50(pretrained=True)
    resnet = torch.nn.Sequential(*(list(resnet.children())[:-1]))  # output shape: [batch, 2048, 1, 1]
    resnet.eval()
    resnet.to(device)

    # Xử lý ảnh query
    print("Đang xử lý ảnh query...")
    query_tensor = load_image(args.query, transform)
    query_feature = extract_feature(query_tensor, resnet, device)

    results = []
    # Duyệt qua các ảnh trong thư mục candidate
    print("Đang xử lý các ảnh candidate...")
    for img_name in os.listdir(args.images_dir):
        img_path = os.path.join(args.images_dir, img_name)
        try:
            candidate_tensor = load_image(img_path, transform)
            candidate_feature = extract_feature(candidate_tensor, resnet, device)
            similarity = F.cosine_similarity(query_feature, candidate_feature, dim=0).item()
            results.append((img_name, similarity))
        except Exception as e:
            print(f"Lỗi khi xử lý {img_path}: {e}")

    # Sắp xếp kết quả theo độ tương đồng giảm dần
    results = sorted(results, key=lambda x: x[1], reverse=True)

    print(f"\nTop {args.top} ảnh tương tự với ảnh query: {args.query}")
    for img_name, sim in results[:args.top]:
        print(f"Image: {img_name} - Similarity: {sim:.4f}")

if __name__ == "__main__":
    main()
