< 실행파일(exe) 생성 >

(1) pyinstaller 설치 ( at 관리자권한 CMD )
	1) 가상환경 활성화 
		PS C:\SOO\Python\day05\EXE> ..\..\penv\Scripts\activate
	2) 설치 
		if python3.8이상
			(penv) C:\~\EXE> python -m pip install https://github.com/pyinstaller/pyinstaller/archive/develop.tar.gz  
		else
			(penv) C:\~\EXE> python -m pip install pyinstaller
		
	3) 설치확인 
		(penv) C:\~\EXE> python -m pip list
		//pyinstaller  확인 

(2) exe 종류별 생성예 
	1) 컨솔이 함께 뜨는 exe ( GUI 없을 때 주로 사용 )
		(penv) C:\~\EXE> pyinstaller --onefile Game.py
	2) 컨솔이 함께 안뜨는 exe ( GUI 있을 때 주로 사용 )
		(penv) C:\~\EXE> pyinstaller --noconsole --onefile Game.py
	3) 아이콘적용 + 컨솔이 함께 뜨는 exe
		(penv) C:\~\EXE> pyinstaller --icon=icon.ico --onefile Game.py
	4) 아이콘적용 + 컨솔이 함께 안뜨는 exe
		(penv) C:\~\EXE> python -m PyInstaller --icon=icon.ico --noconsole --onefile g.py

(3) 실습 
	1) PS C:\SOO\Python\day05\EXE 하위에 다음을 위치시킴 
		- icon.ico
		- g.py
	2) 명령어 
		(penv) C:\~\EXE> python -m PyInstaller --icon=icon.ico --noconsole --onefile g.py

	3) exe확인 
		dist/g.exe

(4) 실행시 윈도우즈 보안에 막힌다면. 
	윈도우즈 시작 > 검색: '스마트 앱 컨트롤' > '끄기'

