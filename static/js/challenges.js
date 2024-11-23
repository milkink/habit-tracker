document.addEventListener('DOMContentLoaded', () => {
  const challengeForm = document.getElementById('challenge-form');
  const challengesContainer = document.querySelector('.challenges-container');

  const fetchChallenges = async () => {
    try {
      const response = await fetch('/challenges');
      const challenges = await response.json();
      
      challengesContainer.innerHTML = challenges.map(challenge => `
        <div class="challenge-card shadow p-3 mb-4 bg-white rounded">
          <h4 class="challenge-title">${challenge.name}</h4>
          <p class="challenge-description">${challenge.description}</p>
          <div class="challenge-details">
            <span class="badge bg-primary">${challenge.start_date} - ${challenge.end_date}</span>
            <span class="badge bg-info">${challenge.participant_count} participants</span>
          </div>
          ${!challenge.isParticipating ? `
            <button class="btn btn-success btn-sm mt-2" 
                    onclick="joinChallenge(${challenge.id})">
              Join Challenge
            </button>
          ` : ''}
          <div class="progress mt-3">
            <div class="progress-bar" role="progressbar" 
                 style="width: ${challenge.completion_rate || 0}%">
              ${challenge.completion_rate || 0}%
            </div>
          </div>
        </div>
      `).join('');
    } catch (error) {
      console.error('Error fetching challenges:', error);
    }
  };

  challengeForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(challengeForm);
    const challengeData = {
      habit_id: formData.get('habit_id'),
      name: formData.get('name'),
      description: formData.get('description'),
      start_date: formData.get('start_date'),
      end_date: formData.get('end_date')
    };

    try {
      const response = await fetch('/challenges', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(challengeData)
      });
      
      if (response.ok) {
        await fetchChallenges();
        challengeForm.reset();
        toastr.success('Challenge created successfully!');
      }
    } catch (error) {
      console.error('Error creating challenge:', error);
      toastr.error('Error creating challenge.');
    }
  });

  window.joinChallenge = async (challengeId) => {
    try {
      const response = await fetch(`/join_challenge/${challengeId}`, {
        method: 'POST'
      });
      if (response.ok) {
        await fetchChallenges();
        toastr.success('Joined challenge successfully!');
      }
    } catch (error) {
      console.error('Error joining challenge:', error);
      toastr.error('Error joining challenge.');
    }
  };

  // Initial load of challenges
  fetchChallenges();
});
