/*
  첨부파일 드래그앤드롭. 글쓰기(form.html)와 글 수정(edit.html)에서 같이 씁니다.
  페이지에 아래 세 요소가 있어야 동작합니다.
    #w-files    서버로 실제 전송되는 <input type="file" name="files" multiple hidden>
    #dropzone   끌어다 놓는 영역
    #file-list  고른 파일 목록이 그려질 곳
*/
(function () {
  var input = document.getElementById("w-files");
  var zone  = document.getElementById("dropzone");
  var list  = document.getElementById("file-list");
  if (!input || !zone || !list) return;

  var files = [];  // 고른 파일 전체. input 과 화면 목록은 항상 이 배열에 맞춥니다.

  // ---- 클릭해서 고르기
  zone.addEventListener("click", function () { input.click(); });

  input.addEventListener("change", function () {
    var picked = Array.prototype.slice.call(input.files);  // 먼저 복사해두고
    input.value = "";   // 비워야 같은 파일을 다시 골라도 change 가 뜹니다
    addFiles(picked);   // 마지막에 sync() 가 input 을 다시 채웁니다
  });

  // ---- 끌어다 놓기
  zone.addEventListener("dragover", function (e) {
    e.preventDefault();  // 이게 있어야 drop 이 허용됩니다
    zone.classList.add("dragover");
  });
  zone.addEventListener("dragleave", function () {
    zone.classList.remove("dragover");
  });
  zone.addEventListener("drop", function (e) {
    e.preventDefault();
    zone.classList.remove("dragover");
    addFiles(e.dataTransfer.files);
  });

  // 드롭존 바깥에 떨어뜨리면 브라우저가 파일을 열어버려 쓰던 글이 날아갑니다.
  window.addEventListener("dragover", function (e) { e.preventDefault(); });
  window.addEventListener("drop", function (e) { e.preventDefault(); });

  // ---- 목록 관리
  function addFiles(newFiles) {
    for (var i = 0; i < newFiles.length; i++) {
      var f = newFiles[i];
      var dup = files.some(function (g) { return g.name === f.name && g.size === f.size; });
      if (!dup) files.push(f);
    }
    sync();
  }

  function removeFile(index) {
    files.splice(index, 1);
    sync();
  }

  // files 배열 → input 과 화면에 반영
  function sync() {
    var dt = new DataTransfer();  // input.files 는 직접 못 고쳐서 새로 만들어 끼웁니다
    files.forEach(function (f) { dt.items.add(f); });
    input.files = dt.files;
    render();
  }

  function render() {
    list.innerHTML = "";
    files.forEach(function (f, i) {
      var row = document.createElement("div");
      row.className = "file";

      var name = document.createElement("span");
      name.className = "name";
      name.textContent = f.name;  // textContent 라서 파일명에 <태그> 가 있어도 안전합니다

      var size = document.createElement("span");
      size.className = "size";
      size.textContent = formatSize(f.size);

      var x = document.createElement("button");
      x.type = "button";  // 없으면 누르는 순간 form 이 제출됩니다
      x.className = "x";
      x.setAttribute("aria-label", "첨부 취소");
      x.textContent = "×";
      x.addEventListener("click", function () { removeFile(i); });

      row.append(name, size, x);
      list.appendChild(row);
    });
  }

  function formatSize(b) {
    if (b < 1024) return b + " B";
    if (b < 1024 * 1024) return (b / 1024).toFixed(1) + " KB";
    return (b / 1024 / 1024).toFixed(1) + " MB";
  }
})();