document.addEventListener('DOMContentLoaded', function() {
    const sqlist_button = document.getElementById('sqlist_button');
    const sqlist = document.getElementById('sqlist');
    const sqlist_close = document.getElementById('sqlist_close');
    
    sqlist_button.addEventListener('click', function() {
      sqlist.style.display = 'block';
    });
    
    sqlist_close.addEventListener('click', function () {
      sqlist.style.display = 'none';
    }
    );
    
    addEventListener('click', function (e) {
      if (e.targer == sqlist) {
        sqlist.style.display = 'none';
      };
    });
    
    
    const question_button = document.getElementById('question_button');
    const question = document.getElementById('question');
    const question_close = document.getElementById('question_close');
    
    question_button.addEventListener('click', function() {
      question.style.display = 'block';
    });
  
    question_close.addEventListener('click', function () {
      question.style.display = 'none';
    });
  
    addEventListener('click', function (e) {
      if (e.targer == question) {
        question.style.display = 'none';
      };
    }); 
  });