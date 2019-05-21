$(document).ready(function () {
  $("#api_account_save").prop("disabled", true);

  $("#input_type").change(function (e) {
    let value = $("#input_type").val();
    if (value == "0") {
      $("#CrossRef_API").addClass("hidden");
      $("#api_account_save").prop("disabled", true);
    } else {
      $("#api_account_save").prop("disabled", false);
      if (value == "crf") {
        $("#CrossRef_API").removeClass("hidden");
      }
      loadCurrentCertData();
    }
  });

  loadDataForInputType();

  $("#api_account_save").click(function (e) {
    save();
  });
});

function addAlert(message) {
    $('#alerts').append(
        '<div class="alert alert-light" id="alert-style">' +
        '<button type="button" class="close" data-dismiss="alert">' +
        '&times;</button>' + message + '</div>');
         }

var save = function () {
  let api_code = $.trim($('#input_type').val());
  let cert_data = $.trim($('#cross_ref_account').val());
  if (!api_code || api_code == '0'){
    alert('Input type is invalid. Please check again.');
    return;
  } else if(!cert_data){
    alert('Account information is invalid. Please check again.');
    return;
  }
  let param = {
    "api_code": api_code,
    "cert_data": cert_data
  }
  $.ajax({
    url: "/api/admin/save_api_cert_data",
    type: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    data: JSON.stringify(param),
    dataType: 'json',
    success: function (data, status) {
      let err_msg = data.error;
      if (err_msg) {
        alert(err_msg);
      } else if (!data.results) {
        alert('Account information is invalid. Please check again.');
      } else {
        addAlert('Account info has been saved successfully.');
      }
    },
    error: function (error) {
      alert(error);
    }
  });
}

var loadDataForInputType = function () {
  $.ajax({
    url: "/api/admin/get_api_cert_type",
    type: 'GET',
    success: function (data) {
      let error = data.error;
      let results = data.results;
      if (error) {
        alert(error);
        return;
      }
      if (!results) {
        alert('Not found certificate data.');
        return;
      }
      let options = '';
      for (let i = 0; i < results.length; i++) {
        options += '<option value="' + results[i].api_code + '">' + results[i].api_name + '</option>';
      }
      const select = $('#input_type');
      select.append(options);
    },
    error: function (error) {
      alert('Error when load account info.');
    }
  });
}

var loadCurrentCertData = function () {
  let get_url = "/api/admin/get_curr_api_cert/" + $('#input_type').val();
  $.ajax({
    url: get_url,
    type: 'GET',
    success: (data, status) => {
      $('#cross_ref_account').val(data.results.cert_data);
    },
    error: function (error) {
      alert('Error when load certificate data of ' + $('#input_type').val());
    }
  });
}
