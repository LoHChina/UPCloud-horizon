var timer = null;
var js_enable_fixed_ip = true;
var getip = function(value){
  return $("#ip0_"+value).val() + '.' + $("#ip1_"+value).val() + '.' +
         $("#ip2_"+value).val() + '.' + $("#ip3_"+value).val();
};

var is_enable_fixed_ip = function(){
  if($("input[name=enable_fixed_ip]").val() == "True") {
    return true;
  }else{
    return false;
  }
};

var ajax_ip = function(value){
  if(timer) {
      window.clearTimeout(timer);
  }

  timer = window.setTimeout(function(){
      var network_id = value;
      var fixed_ip = getip(value);
      $.get(
        $("input[name=webroot]").val() + "check_ip/",
        {
          "network": value,
          "fixed_ip": fixed_ip
        },
        function(text, status){
          if(text == "True"){
              success(value);
          }else{
              fail(value, gettext('The IP you selected has been allocated, please select another one.'));
          }
        }
      );
  }, 300);
};

var success = function(value){
  $("#ok_" + value).show();
  $("#error_" + value).hide();
  $("#msg_" + value).html("").hide();
  $(".modal-footer input[type=submit]").attr('disabled', false);
};

var fail = function(value, err){
  $("#ok_" + value).hide();
  $("#error_" + value).show();
  $("#msg_" + value).html(err).show();
  $(".modal-footer input[type=submit]").attr('disabled', true);
};

var register_actions = function(value){
  $("#dhcp_default_" + value).click(function(){
    for(var i = 0 ; i < 4 ; i++){
      var v = $("#ip" + i + "_"+value);
      if(v.attr('type') != "hidden"){
        v.prop('disabled', true);
      }
    }
    $("input[name=fix_ip" + value + "]").val("");
    update_submit();
  });

  $("#dhcp_specify_" + value).click(function(){
    for(var i = 0 ; i < 4 ; i++){
      var v = $("#ip" + i + "_"+value);
      if(v.attr('type') != "hidden"){
        v.prop('disabled', false);
      }
    }
    $("input[name=fix_ip" + value + "]").val(getip(value));
    update_submit();
  });

  for(var i = 0 ; i < 4 ; i ++){
     var v = $("#ip" + i + "_"+value);
     v.keyup(function(){
        $("input[name=fix_ip" + value + "]").val(getip(value));
        if((v.val() < 255) && (v.val() >= 1)){
            ajax_ip(value);
        }else{
            window.clearTimeout(timer);
            fail(value, gettext("IP Format Error"));
        }
     });
  }
};

var update_submit = function(){
  var result = true;
  if(is_enable_fixed_ip()){
    $("#selected_network li").each(function(index, value){
      var id = $(value).attr("name");
      var selected = $("input[name=radio_" + id +"][checked]").attr("id");
      if(selected.startsWith("dhcp_specify_")){
        result = false;
      }
    });
  }
  $(".modal-footer input[type=submit]").attr('disabled', !result);
};

var clear_all_data = function(){
  $("#selected_network li").each(function(index, value){
    var id = $(value).attr("name");
    $("input[name=radio_" + id + "]")[0].checked = true;
    $("input[name=fix_ip" + id + "]").val("");
    $(".fixip_input").val("").disabled = true;
    $("#ok_" + id).hide();
    $("#error_" + id).hide();
    $("#msg_" + id).html("").hide();
  });
  $("#available_network li").each(function(index, value){
    var id = $(value).attr("name");
    $("input[name=radio_" + id + "]")[0].checked = true;
    $("input[name=fix_ip" + id + "]").val("");
    $(".fixip_input").val("").disabled = true;
    $("#ok_" + id).hide();
    $("#error_" + id).hide();
    $("#msg_" + id).html("").hide();
  });
};

var enable_fixed_func = function(){
  $("#selected_network li").each(function(index, value){
    var id = $(value).attr("name");
    $("div#" + id).show();
  });
};

var disable_fixed_func = function(){
  $("#selected_network li").each(function(index, value){
    var id = $(value).attr("name");
    $("div#" + id).hide();
  });
  $("#available_network li").each(function(index, value){
    var id = $(value).attr("name");
    $("div#" + id).hide();
  });
  clear_all_data();
};


var update_fix_ip = function(){
  var active_networks = $("#selected_network > li").map(function(){
    return $(this).attr("name");
  });
  active_networks.each(function(index, value){
    $("input[name=fix_ip" + value + "]").val(getip(value));
  });
};


    // selected networks
    $("#selected_network li").each(function(index, value){
      register_actions($(value).attr("name"));
    });

    // available networks
    $("#available_network li").each(function(index, value){
      register_actions($(value).attr("name"));
    });

var update_submit = function(){
    var result = true;
    if(is_enable_fixed_ip()){
      $("#selected_network li").each(function(index, value){
        var id = $(value).attr("name");
        var selected = $("input[name=radio_" + id +"][checked]").attr("id");
        if(selected.startsWith("dhcp_specify_")){
          if($("#ok_" + id).ishidden()){
            $(".modal-footer input[type=submit]").attr("disabled", true);
            return;
          }
        }
      });
      $(".modal-footer input[type=submit]").attr("disabled", false);
    }
}

/* global JSEncrypt */
horizon.instances = {
  user_decided_length: false,
  user_volume_size: false,
  networks_selected: [],
  networks_available: [],

  getConsoleLog: function(via_user_submit) {
    var form_element = $("#tail_length"),
      data;

    if (!via_user_submit) {
      via_user_submit = false;
    }

    if(this.user_decided_length) {
      data = $(form_element).serialize();
    } else {
      data = "length=35";
    }

    $.ajax({
      url: $(form_element).attr('action'),
      data: data,
      method: 'get',
      success: function(response_body) {
        $('pre.logs').text(response_body);
      },
      error: function() {
        if(via_user_submit) {
          horizon.clearErrorMessages();
          horizon.alert('error', gettext('There was a problem communicating with the server, please try again.'));
        }
      }
    });
  },

  /*
   * Gets the html select element associated with a given
   * network id for network_id.
   **/
  get_network_element: function(network_id) {
    return $('li > label[for^="id_network_' + network_id + '"]');
  },

  /*
   * Initializes an associative array of lists of the current
   * networks.
   **/
  init_network_list: function () {
    horizon.instances.networks_selected = [];
    horizon.instances.networks_available = [];
    $(this.get_network_element("")).each(function () {
      var $this = $(this);
      var $input = $this.children("input");
      var name = horizon.escape_html($this.text().replace(/^\s+/, ""));
      var network_property = {
        "name": name,
        "id": $input.attr("id"),
        "value": $input.attr("value")
      };
      if ($input.is(":checked")) {
        horizon.instances.networks_selected.push(network_property);
      } else {
        horizon.instances.networks_available.push(network_property);
      }
    });
  },

  /*
   * Generates the HTML structure for a network that will be displayed
   * as a list item in the network list.
   **/
  generate_network_element: function(name, id, value) {
    var $li = $("<li>");
    var $input_str = '';
    if(is_enable_fixed_ip()){
      var i = $("input[name=fix_ip" + value + "]");
      var cidr = i.attr("cidr")
      var net = cidr.split('/')[0];
      var netmask = cidr.split('/')[1];
      $input_str += '<div style="display:none;" class="per_fixip_div" id="' + value + '"><input type="radio" id="dhcp_default_' + value + '" checked name="radio_' + value + '">&nbsp;' + gettext('Default') + '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<input type="radio" id="dhcp_specify_' + value + '" name="radio_' + value + '">&nbsp;';                                           if(netmask >= 8 ){                                                                                                                                                                     $input_str += '<input type="hidden" id="ip0_' + value + '" value="' + net.split('.')[0] + '">' + net.split('.')[0] + ".";                                                          }else{
        $input_str += '<input class="fixip_input" id="ip0_' + value + '" type="text" disabled="disabled">.';
      }
      if(netmask >= 16 ){
        $input_str += '<input type="hidden" id="ip1_' + value + '" value="' + net.split('.')[1] + '">' + net.split('.')[1] + ".";
      }else{
        $input_str += '<input class="fixip_input" id="ip1_' + value + '" type="text" disabled="disabled">.';
      }
      if(netmask >= 24 ){
        $input_str += '<input type="hidden" id="ip2_' + value + '" value="' + net.split('.')[2] + '">' + net.split('.')[2] + ".";
      }else{
        $input_str += '<input class="fixip_input" id="ip2_' + value + '" type="text" disabled="disabled">.';
      }
      $input_str += '<input type="text" id="ip3_' + value + '" class="fixip_input" disabled="disabled">&nbsp;&nbsp;';
      $input_str += '<span id="error_' + value + '" class="glyphicon glyphicon-remove" style="display:none;color:red;"></span><span id="msg_' + value + '" style="color:red"></span>'
      $input_str += '<span id="ok_' + value + '" class="glyphicon glyphicon-ok" style="display:none;"></span></div>';
    }
    $li.attr('name', value).html(name + '<em class="network_id">(' + value + ')</em><a href="#" class="btn btn-primary"></a>' + $input_str);
    return $li;
  },

  /*
   * Generates the HTML structure for the Network List.
   **/
  generate_networklist_html: function() {
    var self = this;
    var available_network = $("#available_network");
    var selected_network = $("#selected_network");
    var updateForm = function() {
      var networkListId = $("#networkListId");
      var lists = networkListId.find("li").attr('data-index',100);
      var active_networks = $("#selected_network > li").map(function(){
        return $(this).attr("name");
      });
      networkListId.find("input:checkbox").removeAttr('checked');
      active_networks.each(function(index, value){
        networkListId.find("input:checkbox[value=" + value + "]")
          .prop('checked', true)
          .parents("li").attr('data-index',index);
      });
      networkListId.find("ul").html(
        lists.sort(function(a,b){
          if( $(a).data("index") < $(b).data("index")) { return -1; }
          if( $(a).data("index") > $(b).data("index")) { return 1; }
          return 0;
        })
      );
    };
    var updateFixip = function() {
      var lists = $("#networkListId li").attr('data-index',100);
      var active_networks = $("#selected_network > li").map(function(){
        return $(this).attr("name");
      });
      active_networks.each(function(index, value){
        $("input[name=fix_ip" + value + "]").val(getip(value));
      });
    };
    $("#networkListSortContainer").show();
    $("#networkListIdContainer").hide();
    self.init_network_list();
    // Make sure we don't duplicate the networks in the list
    available_network.empty();
    $.each(self.networks_available, function(index, value){
      available_network.append(self.generate_network_element(value.name, value.id, value.value));
	    //_start(value.value);
    });
    // Make sure we don't duplicate the networks in the list
    selected_network.empty();
    $.each(self.networks_selected, function(index, value){
      selected_network.append(self.generate_network_element(value.name, value.id, value.value));
    });
    // $(".networklist > li").click(function(){
    //   $(this).toggleClass("ui-selected");
    // });
    $(".networklist > li > a.btn").click(function(e){
      var $this = $(this);
      e.preventDefault();
      e.stopPropagation();
      if($this.parents("ul#available_network").length > 0) {
        $this.parent().appendTo(selected_network);
        var div_id = $this.parent().attr("name");
        if(js_enable_fixed_ip)
          $("#"+div_id).show();
      } else if ($this.parents("ul#selected_network").length > 0) {
        $this.parent().appendTo(available_network);
        var div_id = $this.parent().attr("name");
        $("#"+div_id).hide();
      }
      updateForm();
      update_fix_ip();
      update_submit();
    });
    if ($("#networkListId > div.form-group.error").length > 0) {
      var errortext = $("#networkListId > div.form-group.error span.help-block").text();
      $("#selected_network_label").before($('<div class="dynamic-error">').html(errortext));
    }
    /*$(".networklist").sortable({
      connectWith: "ul.networklist",
      placeholder: "ui-state-highlight",
      distance: 5,
      start:function(){
        selected_network.addClass("dragging");
      },
      stop:function(){
        selected_network.removeClass("dragging");
        updateForm();
      }
    }).disableSelection();*/
	update_submit();
  },

  workflow_init: function() {
    // Initialise the drag and drop network list
    horizon.instances.generate_networklist_html();
    $("#selected_network li").each(function(index, value){
      var div_id = $(value).attr("name");
      $("#"+div_id).show();
    });
    // selected networks
    $("#selected_network li").each(function(index, value){
      register_actions($(value).attr("name"));
    });
    // available networks
    $("#available_network li").each(function(index, value){
      register_actions($(value).attr("name"));
    });
    update_submit();
  }
};

horizon.addInitFunction(horizon.instances.init = function () {
  var $document = $(document);

  $document.on('submit', '#tail_length', function (evt) {
    horizon.instances.user_decided_length = true;
    horizon.instances.getConsoleLog(true);
    evt.preventDefault();
  });

  /* Launch instance workflow */

  // Handle field toggles for the Launch Instance source type field
  function update_launch_source_displayed_fields (field) {
    var $this = $(field);
    var base_type = $this.val();
    var elements_list;

    $this.closest(".form-group").nextAll().hide();

    switch(base_type) {
      case "image_id":
        elements_list = "#id_image_id";
        break;
      case "instance_snapshot_id":
        elements_list = "#id_instance_snapshot_id";
        break;
      case "volume_id":
        elements_list = "#id_volume_id, #id_device_name, #id_delete_on_terminate";
        break;
      case "volume_image_id":
        elements_list = "#id_image_id, #id_volume_size, #id_device_name, #id_delete_on_terminate";
        break;
      case "volume_snapshot_id":
        elements_list = "#id_volume_snapshot_id, #id_device_name, #id_delete_on_terminate";
        break;
    }
    var elements_list_group = $(elements_list).closest(".form-group");
    elements_list_group.addClass("required");
    // marking all the fields in 'elements_list' as mandatory except '#id_device_name'
    $("#id_device_name").closest(".form-group").removeClass("required");
    // showing all the fields in 'elements_list'
    elements_list_group.show();
  }

  $document.on('change', '.workflow #id_source_type', function () {
    update_launch_source_displayed_fields(this);
  });

  $('.workflow #id_source_type').change();
  horizon.modals.addModalInitFunction(function (modal) {
    $(modal).find("#id_source_type").change();
  });

  /*
   Update the device size value to reflect minimum allowed
   for selected image and flavor
   */
  function update_device_size() {
    var volume_size = horizon.Quota.getSelectedFlavor().disk;
    var image = horizon.Quota.getSelectedImage();
    var size_field = $("#id_volume_size");

    if (image !== undefined && image.min_disk > volume_size) {
      volume_size = image.min_disk;
    }
    if (image !== undefined && image.size > volume_size) {
      volume_size = image.size;
    }

    // If the user has manually changed the volume size, do not override
    // unless user-defined value is too small.
    if (horizon.instances.user_volume_size) {
      var user_value = size_field.val();
      if (user_value > volume_size) {
        volume_size = user_value;
      }
    }

    // Make sure the new value is >= the minimum allowed (1GB)
    if (volume_size < 1) {
      volume_size = 1;
    }

    size_field.val(volume_size);
  }

  $document.on('change', '.workflow #id_flavor', function () {
    update_device_size();
  });

  $document.on('change', '.workflow #id_image_id', function () {
    update_device_size();
  });

  $document.on('input', '.workflow #id_volume_size', function () {
    horizon.instances.user_volume_size = true;
    // We only need to listen for the first user input to this field,
    // so remove the listener after the first time it gets called.
    $document.off('input', '.workflow #id_volume_size');
  });

  horizon.instances.decrypt_password = function(encrypted_password, private_key) {
    var crypt = new JSEncrypt();
    crypt.setKey(private_key);
    return crypt.decrypt(encrypted_password);
  };

  $document.on('change', '#id_private_key_file', function (evt) {
    var file = evt.target.files[0];
    var reader = new FileReader();
    if (file) {
      reader.onloadend = function(event) {
        $("#id_private_key").val(event.target.result);
      };
      reader.onerror = function() {
        horizon.clearErrorMessages();
        horizon.alert('error', gettext('Could not read the file'));
      };
      reader.readAsText(file);
    }
    else {
      horizon.clearErrorMessages();
      horizon.alert('error', gettext('Could not decrypt the password'));
    }
  });
  /*
    The font-family is changed because with the default policy the major I
    and minor the l cannot be distinguished.
  */
  $document.on('show.bs.modal', '#password_instance_modal', function () {
    $("#id_decrypted_password").css({
      "font-family": "monospace",
      "cursor": "text"
    });
    $("#id_encrypted_password").css("cursor","text");
    $("#id_keypair_name").css("cursor","text");
  });

  $document.on('click', '#decryptpassword_button', function (evt) {
    var encrypted_password = $("#id_encrypted_password").val();
    var private_key = $('#id_private_key').val();
    if (!private_key) {
      evt.preventDefault();
      $(this).closest('.modal').modal('hide');
    }
    else {
      if (private_key.length > 0) {
        evt.preventDefault();
        var decrypted_password = horizon.instances.decrypt_password(encrypted_password, private_key);
        if (decrypted_password === false || decrypted_password === null) {
          horizon.clearErrorMessages();
          horizon.alert('error', gettext('Could not decrypt the password'));
        }
        else {
          $("#id_decrypted_password").val(decrypted_password);
          $("#decryptpassword_button").hide();
        }
      }
    }
  });

  $document.on('change', '.workflow #id_count', function(){
    if($("input[name=count]").val() != 1) {
      js_enable_fixed_ip = false;
      disable_fixed_func();
    }else{
      js_enable_fixed_ip = true;
      enable_fixed_func();
    }
  });
});
