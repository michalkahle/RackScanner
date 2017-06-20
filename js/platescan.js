var timer = null;
var running = false;
var status_request = null;

function startVialScan() {
   jQuery('#scanvial').click();
}

function startRackScan() {
   jQuery('#scanrack').click();
}

function startUploadCSV() {
  jQuery('#uploadcsv').click();
}

function rack_add_db() {
  if (jQuery('#platebarcode').val()) {
    alert('For new plate no plate barcode should be specified (it will be created automatically).')
  } else {
    startUploadCSV();
  }
}

function rack_update_db() {
  if (!jQuery('#platebarcode').val()) {
    alert('Plate barcode must be specified to update the existing plate.');
  } else {
    startUploadCSV();
  }
}

function scan_status_ok(data, textStatus, jqXHR) {
  var fn = data.trim();
  var lfn = fn.toLowerCase();
  console.log('scan_status_ok:' + fn + ': ' + textStatus);
  if (fn) {
     jQuery('#imagefilename')[0].value = fn;
     if (lfn.indexOf('vial') >= 0) {
       console.log('vial substr found in ' + fn + ' - clicking scanvial');
       //running = true;
       setTimeout(startVialScan, 200); //jQuery('#scanvial').click();
     } else if (lfn.indexOf('rack') >= 0) {
       console.log('rack substr found in ' + fn + ' - clicking scanrack');
       //running = true;
       setTimeout(startRackScan, 200); //jQuery('#scanrack').click();
     } else {
       console.log('no rack or vial substr found in ' + fn + ' - nothing done');
     }
     
  } else {
       
  }
}


function scan_status_error(jqXHR, textStatus, errorThrown) {
  console.log('scan_status_error:' + textStatus);
}

function scan_status_complete() {
  console.log('scan_status_complete');
  status_request = null;
}

function get_status() {
  if (status_request) {
    console.log('get_status - status_request in progress, skipping...')
    return;
  }
  status_request = jQuery.ajax('/wwwcgi.py?action=call&module=platescan&function=status&what=scan',
   { success: scan_status_ok,
     error: scan_status_error,
     dataType: 'text',
     timeout: 1000,
     complete: scan_status_complete
   }

  )
}

function onTimer() {
  //alert('onTimer');
  if (running) { return; }

  if (!jQuery('#timerdisabled')[0].checked) {
     get_status();
  }

}

function refocus() {
   jQuery('#platebarcode').focus();
}

function set_ready() {
   // activate platebarcode input waiting for the barcode scanner to put there the plate barcode
   $('#platebarcode').focus();
}

jQuery(document).ready(function($) {
   timer = setInterval(onTimer, 2000);
   $('#rackadd').click(rack_add_db);
   $('#rackupdate').click(rack_update_db);
   $('#platebarcode').focus();
   $('#ready').click(set_ready);
});
