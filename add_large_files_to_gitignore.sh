: << 'END'
실행방법
(1) chmod +x add_large_files_to_gitignore.sh
(2) ./add_large_files_to_gitignore.sh
END


#!/bin/bash

# 100MB 넘는 파일 찾기
find . -type f -size +100M > large_files.txt

# 기존 .gitignore에 경로 추가 (./ 제거)
while IFS= read -r file; do
  # ./를 제거한 경로 생성
  clean_path="${file#./}"

  # .gitignore에 경로가 없으면 추가
  if ! grep -Fxq "$clean_path" .gitignore; then
    echo "$clean_path" >> .gitignore
  fi
done < large_files.txt

# large_files.txt 삭제
rm large_files.txt

echo "100MB 넘는 파일이 .gitignore에 추가되었습니다."
