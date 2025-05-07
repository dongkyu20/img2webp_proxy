#!/usr/bin/env python
# -*- coding: utf-8 -*-
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import json
import datetime
import uvicorn
from typing import Dict, List, Any

app = FastAPI(title="이미지 크기 감소량 시각화")

# 템플릿 디렉토리 설정
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'templates'))
templates = Jinja2Templates(directory=template_dir)

# 정적 파일 디렉토리 설정
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'static'))

# 필요한 디렉토리 미리 생성
os.makedirs(template_dir, exist_ok=True)
os.makedirs(static_dir, exist_ok=True)

# 목업 데이터 (파이어베이스 DB 연동 전까지 사용)
MOCK_DATA = {
    "images": [
        {
            "domain": "example.com",
            "path": "/images/photo1.jpg",
            "original_size": 1500000,  # 1.5MB
            "webp_size": 450000,      # 450KB
            "timestamp": "2025-05-05T12:30:45"
        },
        {
            "domain": "example.com",
            "path": "/images/photo2.jpg",
            "original_size": 2200000,  # 2.2MB
            "webp_size": 550000,      # 550KB
            "timestamp": "2025-05-05T13:15:20"
        },
        {
            "domain": "blog.example.org",
            "path": "/content/header.jpg",
            "original_size": 3500000,  # 3.5MB
            "webp_size": 800000,      # 800KB
            "timestamp": "2025-05-05T14:05:10"
        }
    ],
    "summary": {
        "total_original": 7200000,    # 7.2MB
        "total_webp": 1800000,        # 1.8MB
        "reduction_percentage": 75    # 75% 감소
    }
}

# 정적 파일 마운트
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """메인 페이지 렌더링"""
    # 여기서 나중에 파이어베이스에서 실제 데이터를 가져올 것입니다
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/stats", response_class=JSONResponse)
async def get_stats():
    """이미지 변환 통계 데이터 API"""
    # 나중에 이 부분을 파이어베이스 DB에서 실제 데이터를 가져오도록 수정
    return MOCK_DATA

@app.get("/api/domains", response_class=JSONResponse)
async def get_domains():
    """도메인별 통계 데이터 API"""
    # 목업 데이터에서 도메인별 통계 계산
    domains = {}
    for image in MOCK_DATA["images"]:
        domain = image["domain"]
        if domain not in domains:
            domains[domain] = {
                "original_size": 0,
                "webp_size": 0,
                "count": 0
            }
        domains[domain]["original_size"] += image["original_size"]
        domains[domain]["webp_size"] += image["webp_size"]
        domains[domain]["count"] += 1
    
    # 각 도메인의 감소율 계산
    result = []
    for domain, stats in domains.items():
        reduction = round((1 - stats["webp_size"] / stats["original_size"]) * 100, 2)
        result.append({
            "domain": domain,
            "original_size": stats["original_size"],
            "webp_size": stats["webp_size"],
            "count": stats["count"],
            "reduction_percentage": reduction
        })
    
    return {"domains": result}

def create_default_template():
    """기본 HTML 템플릿 파일 생성"""
    html_content = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>이미지 크기 감소량 시각화</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .card {
            margin-bottom: 20px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .stats-card {
            text-align: center;
            padding: 20px;
        }
        .reduction-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #28a745;
        }
        .total-saved {
            font-size: 1.8rem;
            color: #007bff;
        }
    </style>
</head>
<body>
    <div class="container mt-5">
        <h1 class="text-center mb-4">이미지 크기 감소량 시각화</h1>
        
        <div class="row">
            <div class="col-md-4">
                <div class="card stats-card">
                    <h3>총 감소율</h3>
                    <div class="reduction-value" id="total-reduction">로딩 중...</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card stats-card">
                    <h3>절약된 크기</h3>
                    <div class="total-saved" id="total-saved">로딩 중...</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card stats-card">
                    <h3>처리된 이미지</h3>
                    <div class="total-saved" id="image-count">로딩 중...</div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">도메인별 감소율</div>
                    <div class="card-body">
                        <canvas id="domainChart"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">원본 vs WebP 크기 비교</div>
                    <div class="card-body">
                        <canvas id="sizeComparisonChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">최근 처리된 이미지</div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>도메인</th>
                                        <th>경로</th>
                                        <th>원본 크기</th>
                                        <th>WebP 크기</th>
                                        <th>감소율</th>
                                        <th>처리 시간</th>
                                    </tr>
                                </thead>
                                <tbody id="recent-images">
                                    <tr>
                                        <td colspan="6" class="text-center">로딩 중...</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="/static/js/charts.js"></script>
</body>
</html>
"""
    
    with open(os.path.join(template_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)

def create_default_js():
    """기본 JavaScript 파일 생성"""
    js_content = """// 데이터 포맷 함수
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// 도메인별 감소율 차트 생성
function createDomainChart(domains) {
    const ctx = document.getElementById('domainChart').getContext('2d');
    
    const labels = domains.map(d => d.domain);
    const reductions = domains.map(d => d.reduction_percentage);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '감소율 (%)',
                data: reductions,
                backgroundColor: 'rgba(54, 162, 235, 0.7)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: '감소율 (%)'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: '도메인별 이미지 크기 감소율'
                }
            }
        }
    });
}

// 크기 비교 차트 생성
function createSizeComparisonChart(summary) {
    const ctx = document.getElementById('sizeComparisonChart').getContext('2d');
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['WebP 크기', '절약된 크기'],
            datasets: [{
                data: [summary.total_webp, summary.total_original - summary.total_webp],
                backgroundColor: [
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(255, 99, 132, 0.7)'
                ],
                borderColor: [
                    'rgba(75, 192, 192, 1)',
                    'rgba(255, 99, 132, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            plugins: {
                title: {
                    display: true,
                    text: '원본 대비 WebP 이미지 크기 비율'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + formatBytes(context.raw);
                        }
                    }
                }
            }
        }
    });
}

// 최근 처리된 이미지 목록 업데이트
function updateRecentImages(images) {
    const tbody = document.getElementById('recent-images');
    tbody.innerHTML = '';
    
    images.forEach(img => {
        const row = document.createElement('tr');
        
        const reduction = ((1 - img.webp_size / img.original_size) * 100).toFixed(2);
        const date = new Date(img.timestamp);
        
        row.innerHTML = `
            <td>${img.domain}</td>
            <td>${img.path}</td>
            <td>${formatBytes(img.original_size)}</td>
            <td>${formatBytes(img.webp_size)}</td>
            <td>${reduction}%</td>
            <td>${date.toLocaleString()}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// 요약 정보 업데이트
function updateSummary(summary, imageCount) {
    document.getElementById('total-reduction').textContent = `${summary.reduction_percentage}%`;
    document.getElementById('total-saved').textContent = formatBytes(summary.total_original - summary.total_webp);
    document.getElementById('image-count').textContent = imageCount;
}

// 데이터 로드 및 차트 생성
async function loadData() {
    try {
        // 통계 데이터 가져오기
        const statsResponse = await fetch('/api/stats');
        const statsData = await statsResponse.json();
        
        // 도메인별 데이터 가져오기
        const domainsResponse = await fetch('/api/domains');
        const domainsData = await domainsResponse.json();
        
        // 차트 생성
        createDomainChart(domainsData.domains);
        createSizeComparisonChart(statsData.summary);
        
        // 테이블 데이터 업데이트
        updateRecentImages(statsData.images);
        
        // 요약 정보 업데이트
        updateSummary(statsData.summary, statsData.images.length);
        
    } catch (error) {
        console.error('데이터 로드 중 오류 발생:', error);
    }
}

// 페이지 로드 시 데이터 로드
document.addEventListener('DOMContentLoaded', loadData);

// 5분마다 데이터 자동 갱신
setInterval(loadData, 5 * 60 * 1000);
"""
    
    js_dir = os.path.join(static_dir, 'js')
    os.makedirs(js_dir, exist_ok=True)
    
    with open(os.path.join(js_dir, 'charts.js'), 'w', encoding='utf-8') as f:
        f.write(js_content)


def create_template_and_static_files():
    """템플릿과 정적 파일 생성"""
    # 디렉토리는 이미 앱 초기화 시 생성됨
    
    # 템플릿 파일이 없으면 기본 템플릿 생성
    index_template_path = os.path.join(template_dir, 'index.html')
    if not os.path.exists(index_template_path):
        # 상위 디렉토리 생성
        os.makedirs(os.path.dirname(index_template_path), exist_ok=True)
        create_default_template()
    
    # 정적 파일이 없으면 기본 스크립트 생성
    js_path = os.path.join(static_dir, 'js', 'charts.js')
    if not os.path.exists(js_path):
        # 상위 디렉토리 생성
        os.makedirs(os.path.dirname(js_path), exist_ok=True)
        create_default_js()

if __name__ == '__main__':
    create_template_and_static_files()
    print(f"웹 서버 시작: http://127.0.0.1:8000/")
    uvicorn.run("view_page:app", host="127.0.0.1", port=8000, reload=True)

