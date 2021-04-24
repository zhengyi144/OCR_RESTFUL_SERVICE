
var srcImage1="";
var srcImage2="";
var orientation=1;
var operatorType="ocr";
var imageType=1;
/**
 * 获取图片方向:1,3,6,8分别代表0,180，顺时90，逆时90
 */
function getOrientation(file, callback) {
    var reader = new FileReader();
    reader.onload = function(event) {
      var view = new DataView(event.target.result);
   
      if (view.getUint16(0, false) != 0xFFD8) return callback(-2);
   
      var length = view.byteLength,
          offset = 2;
   
      while (offset < length) {
        var marker = view.getUint16(offset, false);
        offset += 2;
   
        if (marker == 0xFFE1) {
          if (view.getUint32(offset += 2, false) != 0x45786966) {
            return callback(-1);
          }
          var little = view.getUint16(offset += 6, false) == 0x4949;
          offset += view.getUint32(offset + 4, little);
          var tags = view.getUint16(offset, little);
          offset += 2;
   
          for (var i = 0; i < tags; i++)
            if (view.getUint16(offset + (i * 12), little) == 0x0112)
              return callback(view.getUint16(offset + (i * 12) + 8, little));
        }
        else if ((marker & 0xFF00) != 0xFF00) break;
        else offset += view.getUint16(offset, false);
      }
      return callback(-1);
    };
   
    reader.readAsArrayBuffer(file.slice(0, 64 * 1024));
};

function selectImage(fileObj){
    operatorType=$("input[name='imageType']:checked").val();
    
    if(!fileObj.files||!fileObj.files[0]){
        return;
    }
    var file=fileObj.files[0];
    var pictureType=file.type.split("/")[1];
    if(pictureType=="bmp" ||pictureType=="tiff"||pictureType=="jpeg"||pictureType=="jpg"||pictureType=="png"){
        EXIF.getData(file, function () {
            orientation = EXIF.getTag(this, 'Orientation');//获取Orientation信息
            var reader = new FileReader();
            reader.onload = function (evt) {
                if(operatorType=="face" && srcImage1!=""){
                    srcImage2=evt.target.result;
                    $("#dstImage").attr("src",srcImage2);
                    imageType=2;
                }
                else{
                    imageType=1;
                    srcImage1 = evt.target.result;
                    $("#srcImage").attr("src",srcImage1);
                }
            }
            reader.readAsDataURL(file);
        });
    }
}

function uploadImage(){
    var image="";
    if (imageType==1){
        image=srcImage1;
    }else{
        image=srcImage2;
    }
    $.ajax({
        type:'POST',
        url: '/uploadImage', 
        data: {"image":image ,"orientation":orientation,"imageType":imageType},
        async: false,
        dataType: 'json',
        success: function(data){
           alert("上传成功！");
        }
    });
}

function ocrDetectRecognise(){
    $.ajax({
        type:'GET',
        url: '/paddleOcrOperator', 
        dataType: 'json',
        success: function(data){
            $("#dstImage").attr("src",'data:image/jpeg;base64,'+data["image"]);
        },
        
        error: function(err){
          alert("检测报错！");
        } 
    });
}

function faceDetect(){
    $.ajax({
        type:'GET',
        url: '/faceDetectOperator', 
        dataType: 'json',
        success: function(data){
            $("#dstImage").attr("src",'data:image/jpeg;base64,'+data["image"]);
        },
        
        error: function(err){
          alert("检测报错！");
        } 
    });
}

function faceRecognise(){
    if(srcImage2==""){
        alert("请上传比对人像！");
        return ;
    }
    $.ajax({
        type:'GET',
        url: '/faceRecogniseOperator', 
        dataType: 'json',
        success: function(data){
            $("#cmpResult").val("人脸比对是否相同："+data["result"]+",相似度:"+data["distance"]);
        }
    });
}