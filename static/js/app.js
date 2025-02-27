let currentArticle = null;

// Random Article Functions
function fetchRandomArticle() {
  fetch('/get_random_article')
    .then(response => response.json())
    .then(data => {
      currentArticle = data;
      document.getElementById('article-text').value = data.text;
      document.getElementById('article-section').style.display = 'block';
      document.getElementById('guess-buttons').style.display = 'flex';
      document.getElementById('result-card').style.display = 'none';
    });
}

function submitGuess(guess) {
  if (!currentArticle) return;
  
  fetch('/check_guess', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      index: currentArticle.index,
      guess: guess
    })
  })
  .then(response => response.json())
  .then(result => {
    const resultCard = document.getElementById('result-card');
    const resultText = document.getElementById('result-text');
    const actualClass = document.getElementById('actual-class');

    resultText.textContent = result.correct ? "🎉 Correct!" : "❌ Try Again";
    resultText.style.color = result.correct ? '#10b981' : '#ef4444';
    actualClass.textContent = result.actual_class;
    actualClass.style.color = result.actual_class === 'Real' ? '#10b981' : '#ef4444';
    
    document.getElementById('guess-buttons').style.display = 'none';
    resultCard.style.display = 'block';
  });
}

// Article Verification Functions
function verifyArticle() {
  const text = document.getElementById('verify-text').value;
  if (!text.trim()) return;

  const resultDiv = document.getElementById('verdict-result');
  resultDiv.classList.add('hidden');

  fetch('/verify_article', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text: text })
  })
  .then(response => response.json())
  .then(data => {
    if (data.error) {
      alert(`Error: ${data.error}`);
      return;
    }

    document.getElementById('verdict-text').textContent = data.verdict;
    const sourcesList = document.getElementById('sources-list');
    sourcesList.innerHTML = data.sources.map(url => 
      `<li><a href="${url}" target="_blank">${url}</a></li>`
    ).join('');
    
    resultDiv.classList.remove('hidden');
  });
}