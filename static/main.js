function getBotResponse() {
  var rawText = $("#textInput").val();
  var userHtml = '<p class="userText"><span>' + rawText + "</span></p>";
  $("#textInput").val("");
  $("#chatbox").append(userHtml);
  document
    .getElementById("userInput")
    .scrollIntoView({ block: "start", behavior: "smooth" });
  $.get("/get", { msg: rawText }).done(function(data) {
    var botHtml = '<p class="botText"><span>' + data + "</span></p>";
    $("#chatbox").append(botHtml);
    document
      .getElementById("userInput")
      .scrollIntoView({ block: "start", behavior: "smooth" });
  });
}
$("#textInput").keypress(function(e) {
  if (e.which == 13) {
    getBotResponse();
  }
});


const chatbox = jQuery.noConflict();

chatbox(() => {
  chatbox(".chatbox-open").click(() =>
    chatbox(".chatbox-popup, .chatbox-close").fadeIn()
  );

  chatbox(".chatbox-close").click(() =>
    chatbox(".chatbox-popup, .chatbox-close").fadeOut()
  );

  chatbox(".chatbox-maximize").click(() => {
    chatbox(".chatbox-popup, .chatbox-open, .chatbox-close").fadeOut();
    chatbox(".chatbox-panel").fadeIn();
    chatbox(".chatbox-panel").css({ display: "flex" });
  });

  chatbox(".chatbox-minimize").click(() => {
    chatbox(".chatbox-panel").fadeOut();
    chatbox(".chatbox-popup, .chatbox-open, .chatbox-close").fadeIn();
  });

  chatbox(".chatbox-panel-close").click(() => {
    chatbox(".chatbox-panel").fadeOut();
    chatbox(".chatbox-open").fadeIn();
  });
});