
/* Действия после загрузки документа */
$(document).ready(function() {

    /* Автоскрытие и удаление flash-сообщения через 5 секунд. Если оно есть. */
    $("#flash").oneTime(5000, CloseFlash);

    // Установка кнопки "Отказаться"
    $(".backbutton").click(function(){history.back();});

});

/* В форме подачи жалобы подгрузка информации о выбранной заявке */
$(document).ready(function() {
    if ($("#complainform #id").val()!="") LoadOrderInfo($("#complainform #id").val(),"#complainorderinfo");
    $("#complainform #id").change(function(){LoadOrderInfo($("#complainform #id").val(),"#complainorderinfo");});
});


// Подгрузка исполнителей в форме смены статуса заявки
$(document).ready(function() {
  $("#chooseact #div_id").change(function() {
    $("#perfs *").remove();
    $("#perfs").text("");
    $("<p>").addClass("loading").text("Загрузка...").appendTo("#perfs");
    $.getJSON("/division/"+$(this).val()+"/getperformers",{},
      function(json){
        $("#perfs p.loading").remove();
        $.each(json, function (i, item) {
            $('<input />').attr("type", "checkbox").attr("name", "performers").attr("value", item.id).appendTo("#perfs");
            $('<span>').text(item.name).appendTo("#perfs");
            $('<br/>').appendTo("#perfs");
        });
      });
  });
});

// Функция загружает инфу о заявке в HTML и притыкает её куда скажешь
function LoadOrderInfo(id, whereload) {
  $(whereload+" *").remove();
  if (id) {
    $("<p>").addClass("loading").text("Загрузка...").appendTo(whereload);
    $(whereload).load("/order/"+id+"/getinfo",{},function(){$("p.loading").remove();}, "html");
  }
}

/* Функция для скрытия и удаления flash-сообщения (то, которое в жёлтой рамочке) */
function CloseFlash () {
    $("#flash").hide(500, function () {
        $("#flash").remove();
    });
};

// Автозаполнение поля "логин" в форме создания пользователя
var disableLoginAutoFill;

$(document).ready(function() {
    disableLoginAutoFill = false;
    $("#usercreationform #surname").keypress(AutoFillUserLogin).keypress();
    $("#usercreationform #name").keypress(AutoFillUserLogin).keypress();
    $("#usercreationform #patronymic").keypress(AutoFillUserLogin).keypress();
    $("#usercreationform #login").change(function () { disableLoginAutoFill = true; });
});

function AutoFillUserLogin () {
    if (!disableLoginAutoFill) {
        surname = $("#usercreationform #surname").val() || "";
        name = $("#usercreationform #name").val() || "";
        patr = $("#usercreationform #patronymic").val() || "";
        $("#usercreationform #login").val( surname + (name[0] || "") + (patr[0] || "") );
    }
}


// Добавление/удаление инвентарных номеров
$(document).ready(function() {
    $("#invs #addinv").click(function () {
        $(this).before('<input id="inventories" maxlength="12" name="inventories" type="text" value="" /> <button type="button" class="removeinv">Удалить</button><br />');
    });
    $("#invs button.removeinv").live("click", function () {
        $(this).prev().remove(); // Удаляем из DOM поле с инвентарников
        $(this).next().remove(); // Удаляем из DOM последующий <br />
        $(this).remove();        // Удаляем из DOM саму кнопку "Удалить"
    });
});

// Подгрузка категорий в соответствии с текущей надкатегорией
$(document).ready(function() {
    ucsel = $("#orderform #upcat_id");
    csel = $("#orderform #cat_id");
    ucsel.change(function() {
        $("#orderform #cat_id option+option").remove();
        if (ucsel.val() == "None")
            return;  
        loading = $("<p>").addClass("loadingsmall").text("Загрузка...");
        csel.hide();
        csel.before(loading);
        $.getJSON("/order/"+ucsel.val()+"/getcatsforupcat", function(data) {
            $.each(data, function(i,item) {
                $("<option>").attr("value", item.id).text(item.text).appendTo(csel);
            });
            loading.remove();
            csel.show();
        });
    });
});
