/*
  제목·내용이 공백뿐이면 제출 전에 막습니다.
  서버까지 갔다가 폼이 다시 그려지면 고른 첨부파일이 사라지기 때문입니다.
  글쓰기(form.html)와 글 수정(edit.html)에서 같이 씁니다.
  #w-title, #w-body 에 required 가 있어야 말풍선이 뜹니다.
*/
(function () {
  var title = document.getElementById("w-title");
  var body  = document.getElementById("w-body");
  if (!title || !body) return;

  title.form.addEventListener("submit", function (e) {
    var fields = [title, body];
    for (var i = 0; i < fields.length; i++) {
      if (fields[i].value.trim() === "") {
        e.preventDefault();
        fields[i].value = "";
        fields[i].reportValidity();
        return;
      }
    }
  });
})();