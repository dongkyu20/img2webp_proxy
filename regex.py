import re

def transform_image_urls(content):
    # JS 문자열 내부와 일반 HTML 모두에 대응하는 강화된 패턴
    # 1. HTML에서의 이미지 태그 처리
    html_pattern = r'<img\s+([^>]*?)src=["\']((?:.+/)?([^/]+?)\.(jpg|jpeg|png))["\']([^>]*)>'
    
    # 2. JS 문자열 내부의 이미지 태그 처리 (예: "<img ... src=\"path/file.png\" ...">")
    js_pattern = r'["\']\s*<img\s+([^>]*?)src=\\["\']((?:.+/)?([^/]+?)\.(jpg|jpeg|png))\\["\']([^>]*?)>["\']'
    
    # 3. JS 문자열 내 변수 연결 패턴 (예: "<img ... src=\"" + arkPath + "/img/file.png\" ...">")
    js_complex_pattern = r'["\']\s*<img\s+([^>]*?)src=\\["\']([^"\']+)\\["\'](\s*\+\s*[^+]+\+\s*\\["\'])?([^/]+?)\.(jpg|jpeg|png)\\["\']([^>]*?)>["\']'
    
    def replace_html_match(match):
        before_src = match.group(1)  # src 속성 전의 속성들
        filename = match.group(3)    # 파일명
        ext = match.group(4)         # 확장자
        after_src = match.group(5)   # src 속성 후의 속성들
        return f'<img {before_src}src="https://storage.cloud.google.com/cdn.ecarbon.kr/{filename}.webp"{after_src}>'
    
    def replace_js_match(match):
        before_src = match.group(1)  # src 속성 전의 속성들
        filename = match.group(3)    # 파일명
        ext = match.group(4)         # 확장자
        after_src = match.group(5)   # src 속성 후의 속성들
        return f'"<img {before_src}src=\\"https://storage.cloud.google.com/cdn.ecarbon.kr/{filename}.webp\\"{after_src}>"'
    
    def replace_js_complex_match(match):
        # 복잡한 JS 문자열 연결 패턴 처리
        before_src = match.group(1)   # src 속성 전의 속성들
        path_part = match.group(2)    # 경로의 첫 부분
        var_part = match.group(3) or "" # 변수 연결 부분 (+로 연결된 변수)
        filename = match.group(4)     # 파일명
        after_src = match.group(6)    # src 속성 후의 속성들
        
        # 복잡한 구조 유지하면서 확장자만 webp로 변경
        if var_part:
            # 변수 연결 부분이 있는 경우 (예: arkPath + "/img/)
            return f'"<img {before_src}src=\\"{path_part}\\"{var_part}{filename}.webp\\"{after_src}>"'
        else:
            # 단순 경로인 경우
            return f'"<img {before_src}src=\\"https://storage.cloud.google.com/cdn.ecarbon.kr/{filename}.webp\\"{after_src}>"'
    
    # 패턴 순서대로 적용
    modified_content = re.sub(html_pattern, replace_html_match, content)
    modified_content = re.sub(js_pattern, replace_js_match, modified_content)
    modified_content = re.sub(js_complex_pattern, replace_js_complex_match, modified_content)
    
    return modified_content

# 테스트 예제
if __name__ == "__main__":
    # 일반 HTML
    html_example = '<img style="position: absolute; margin: 5px 2px;" src="/images/common/menu/menu_blank_img.png" alt="새창으로 연결">'
    
    # JS 문자열 내부의 HTML
    js_example = 'img id=\"" + imgDownId + "\" src=\"" + arkPath + "/img/arrow_auto_main.png\" width=\"16\" tabindex=\"0\" alt=\"자동완성펼치기\"> '
    
    # 복잡한 JS 문자열 (변수 연결 포함)
    js_complex_example = '"<img id=\\"" + imgDownId + "\\" src=\\"" + arkPath + "/img/arrow_auto_main.png\\" width=\\"16\\" tabindex=\\"0\\" alt=\\"자동완성펼치기\\">"'
    
    print("HTML 예제 변환:")
    print(transform_image_urls(html_example))
    print("\nJS 문자열 예제 변환:")
    print(transform_image_urls(js_example))
    print("\n복잡한 JS 문자열 예제 변환:")
    print(transform_image_urls(js_complex_example))