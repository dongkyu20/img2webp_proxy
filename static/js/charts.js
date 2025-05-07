// 데이터 포맷 함수
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
