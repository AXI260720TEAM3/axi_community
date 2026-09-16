/*
  공통 쪽지 팝업. base.html 이 로그인한 사용자에게만 불러옵니다.
  class="message-open" 인 링크를 누르면 열리고, data-receiver(아이디)와 data-name(이름)을 읽습니다.
  링크의 href 는 쪽지함 주소로 두세요. JS 가 막히면 그 주소로 이동해 그대로 보낼 수 있습니다.
*/
(function () {
  var modal = document.getElementById("message-modal");
  if (!modal) return;   // 로그인하지 않은 화면에는 팝업이 없습니다

  var form = document.getElementById("message-modal-form");
  var receiver = document.getElementById("message-receiver");
  var receiverName = document.getElementById("message-receiver-name");
  var content = document.getElementById("message-content");
  var result = document.getElementById("message-result");

  function openModal(link) {
    receiver.value = link.dataset.receiver;
    receiverName.value = link.dataset.name;
    content.value = "";
    showResult("");
    // 보낸 뒤 잠가둔 버튼을 다시 풀어줍니다.
    // 이게 없으면 한 번 보낸 다음에는 새로고침 전까지 다시 보낼 수 없습니다.
    setSending(false);
    modal.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
    content.focus();
  }

  function closeModal() {
    modal.classList.remove("open");
    modal.setAttribute("aria-hidden", "true");
  }

  function showResult(text, isError) {
    result.textContent = text;
    result.className = isError ? "message-result error" : "message-result";
    result.style.display = text ? "block" : "none";
  }

  function setSending(sending) {
    var button = form.querySelector("button[type=submit]");
    if (button) button.disabled = sending;
  }

  // 문서 전체에서 클릭을 받습니다. 링크가 몇 개든, 어느 화면이든 한 번에 처리됩니다.
  document.addEventListener("click", function (e) {
    var link = e.target.closest(".message-open");
    if (!link) return;
    e.preventDefault();
    openModal(link);
  });

  document.getElementById("message-modal-close").addEventListener("click", closeModal);
  document.getElementById("message-modal-cancel").addEventListener("click", closeModal);
  modal.addEventListener("click", function (e) { if (e.target === modal) closeModal(); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && modal.classList.contains("open")) closeModal();
  });

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    if (!content.value.trim()) {
      showResult("쪽지 내용을 입력해주세요.", true);
      return;
    }

    setSending(true);
    showResult("쪽지를 보내는 중입니다.");

    try {
      var response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        credentials: "same-origin",
        headers: {"X-Requested-With": "XMLHttpRequest"}
      });

      // 로그인 페이지 같은 HTML 이 오면 여기서 오류가 나고 catch 로 넘어갑니다
      var data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.error || "");

      showResult("쪽지를 보냈습니다.");
      setTimeout(closeModal, 700);
    } catch (error) {
      showResult(error.message || "쪽지를 보내지 못했습니다. 다시 시도해주세요.", true);
      setSending(false);
    }
  });
})();
