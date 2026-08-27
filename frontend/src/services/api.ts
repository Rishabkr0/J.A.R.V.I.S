
export const getHealth = async () => {
  try {
    const response = await fetch('http://localhost:8000/health');
    if (!response.ok) throw new Error('Network response was not ok');
    return await response.json();
  } catch (error) {
    console.error('Error fetching health:', error);
    throw error;
  }
};
