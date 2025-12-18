import { useState } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [selectedAnime, setSelectedAnime] = useState(null)
  const [loading, setLoading] = useState(false)
  const [enriching, setEnriching] = useState(false)
  const [enrichingProgress, setEnrichingProgress] = useState({ current: 0, total: 0 })

  // 1. SEARCH FUNCTION
  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query) return
    
    setLoading(true)
    try {
      // Connects to your Python Backend
      const res = await axios.get(`http://127.0.0.1:8000/search?query=${query}`)
      setSearchResults(res.data.results)
      setRecommendations([]) // Clear old recommendations
      setSelectedAnime(null)
    } catch (error) {
      console.error("Error searching:", error)
    }
    setLoading(false)
  }

  // 2. ENRICHMENT FUNCTION - Fetch images and descriptions from Jikan API
  // Jikan API has rate limits: 3 requests/second, so we add delays
  const fetchAnimeDetails = async (animeId, animeTitle = null, delay = 0) => {
    // Add delay to respect rate limits (3 requests/second = ~333ms between requests)
    if (delay > 0) {
      await new Promise(resolve => setTimeout(resolve, delay))
    }
    
    try {
      const res = await axios.get(`https://api.jikan.moe/v4/anime/${animeId}`, {
        timeout: 5000 // 5 second timeout
      })
      const data = res.data.data
      return {
        image: data.images?.jpg?.large_image_url || data.images?.jpg?.image_url || null,
        description: data.synopsis || data.background || 'No description available.',
        score: data.score || null,
        episodes: data.episodes || null,
        year: data.year || null
      }
    } catch (error) {
      // Handle rate limiting (429)
      if (error.response?.status === 429) {
        console.warn(`Rate limited for anime ${animeId}, waiting...`)
        // Wait longer and retry once
        await new Promise(resolve => setTimeout(resolve, 2000))
        try {
          const retryRes = await axios.get(`https://api.jikan.moe/v4/anime/${animeId}`, {
            timeout: 5000
          })
          const retryData = retryRes.data.data
          return {
            image: retryData.images?.jpg?.large_image_url || retryData.images?.jpg?.image_url || null,
            description: retryData.synopsis || retryData.background || 'No description available.',
            score: retryData.score || null,
            episodes: retryData.episodes || null,
            year: retryData.year || null
          }
        } catch {
          console.warn(`Retry failed for anime ${animeId}`)
        }
      }
      
      // If ID lookup fails (404) and we have a title, try searching by title
      if (error.response?.status === 404 && animeTitle) {
        try {
          await new Promise(resolve => setTimeout(resolve, 350)) // Rate limit delay
          const searchRes = await axios.get(`https://api.jikan.moe/v4/anime?q=${encodeURIComponent(animeTitle)}&limit=1`, {
            timeout: 5000
          })
          if (searchRes.data.data && searchRes.data.data.length > 0) {
            const data = searchRes.data.data[0]
            return {
              image: data.images?.jpg?.large_image_url || data.images?.jpg?.image_url || null,
              description: data.synopsis || data.background || 'No description available.',
              score: data.score || null,
              episodes: data.episodes || null,
              year: data.year || null
            }
          }
        } catch {
          console.warn(`Search by title also failed for "${animeTitle}"`)
        }
      }
      
      console.warn(`Could not fetch details for anime ${animeId} (${animeTitle || 'unknown'}):`, error.response?.status || error.message)
      return {
        image: null,
        description: 'Description not available.',
        score: null,
        episodes: null,
        year: null
      }
    }
  }

  // 3. RECOMMEND FUNCTION
  const getRecommendations = async (animeId, animeTitle) => {
    setLoading(true)
    try {
      // 1. Get Recommendations from Python
      const res = await axios.get(`http://127.0.0.1:8000/recommend/${animeId}`)
      const rawRecommendations = res.data.recommendations
      
      // 2. Set the "Hero" anime (the one you clicked)
      setSelectedAnime({ id: animeId, title: animeTitle })
      setSearchResults([]) // Clear search results to show the recommendations
      
      // 3. Enrich with images and descriptions from Jikan API
      // Process sequentially with delays to respect rate limits (3 req/sec)
      setEnriching(true)
      setEnrichingProgress({ current: 0, total: rawRecommendations.length })
      const enrichedRecommendations = []
      
      for (let i = 0; i < rawRecommendations.length; i++) {
        const rec = rawRecommendations[i]
        // Add delay between requests (350ms = ~2.8 requests/second, safe margin)
        const delay = i > 0 ? 350 : 0
        const details = await fetchAnimeDetails(rec.id, rec.title, delay)
        
        enrichedRecommendations.push({
          ...rec,
          image: details.image,
          description: details.description,
          malScore: details.score,
          episodes: details.episodes,
          year: details.year
        })
        
        // Update progress
        setEnrichingProgress({ current: i + 1, total: rawRecommendations.length })
        
        // Update UI progressively as we load (better UX)
        if (i === 0 || (i + 1) % 3 === 0) {
          setRecommendations([...enrichedRecommendations])
        }
      }
      
      setRecommendations(enrichedRecommendations)
      setEnriching(false)
      setEnrichingProgress({ current: 0, total: 0 })
    } catch (error) {
      console.error("Error getting recommendations:", error)
      setEnriching(false)
      // THE FIX: Tell the user what happened
      if (error.response && error.response.status === 404) {
        alert(`Sorry! The AI hasn't watched "${animeTitle}" yet (Not enough training data). Try a classic like Naruto or One Piece!`)
      } else {
        alert("Something went wrong connecting to the server.")
      }
    }
    setLoading(false)
  }

  return (
    <div className="app-container">
      {/* HEADER */}
      <header>
        <h1>🎌 Anime Recommender</h1>
        <p>Powered by Machine Learning (SVD)</p>
      </header>

      {/* SEARCH BAR */}
      <form onSubmit={handleSearch} className="search-box">
        <input 
          type="text" 
          placeholder="Enter an anime (e.g., Naruto)..." 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" disabled={loading}>
          {loading ? (
            <span className="loading"></span>
          ) : (
            "Search"
          )}
        </button>
      </form>

      {/* SEARCH RESULTS GRID */}
      {searchResults.length > 0 && (
        <div className="results-section">
          <h3>Select an Anime:</h3>
          <div className="grid">
            {searchResults.map((anime) => (
              <div 
                key={anime.id} 
                className="card" 
                onClick={() => getRecommendations(anime.id, anime.title)}
              >
                <h4>{anime.title}</h4>
                <span className="id-badge">ID: {anime.id}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* LOADING STATE */}
      {loading && !searchResults.length && !recommendations.length && (
        <div style={{ marginTop: '3rem' }}>
          <div className="loading" style={{ margin: '0 auto', width: '40px', height: '40px', borderWidth: '4px' }}></div>
        </div>
      )}

      {/* RECOMMENDATIONS GRID */}
      {selectedAnime && (
        <div className="recommendations-section">
          {loading ? (
            <div style={{ marginTop: '2rem' }}>
              <div className="loading" style={{ margin: '0 auto', width: '40px', height: '40px', borderWidth: '4px' }}></div>
              <p style={{ marginTop: '1rem', color: 'var(--text-secondary)' }}>Finding recommendations...</p>
            </div>
          ) : enriching ? (
            <div style={{ marginTop: '2rem' }}>
              <div className="loading" style={{ margin: '0 auto', width: '40px', height: '40px', borderWidth: '4px' }}></div>
              <p style={{ marginTop: '1rem', color: 'var(--text-secondary)' }}>
                Loading images and details... ({enrichingProgress.current}/{enrichingProgress.total})
              </p>
              {enrichingProgress.total > 0 && (
                <div style={{ 
                  width: '300px', 
                  maxWidth: '90%', 
                  height: '4px', 
                  background: 'rgba(148, 163, 184, 0.2)', 
                  borderRadius: '2px', 
                  margin: '1rem auto 0',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    width: `${(enrichingProgress.current / enrichingProgress.total) * 100}%`,
                    height: '100%',
                    background: 'linear-gradient(90deg, var(--accent), var(--success))',
                    transition: 'width 0.3s ease'
                  }}></div>
                </div>
              )}
            </div>
          ) : recommendations.length > 0 ? (
            <>
              <h2>Because you liked <span>{selectedAnime.title}</span>:</h2>
              
              <div className="grid recommendations-grid">
                {recommendations.map((rec) => (
                  <div key={rec.id} className="card recommendation-card">
                    <div className="card-image">
                      {rec.image ? (
                        <img src={rec.image} alt={rec.title} onError={(e) => {
                          e.target.style.display = 'none';
                        }} />
                      ) : (
                        <div className="image-placeholder">🎌</div>
                      )}
                      <div className="match-score">
                        {(rec.score * 100).toFixed(1)}% Match
                      </div>
                    </div>
                    <div className="card-content">
                      <h4>{rec.title}</h4>
                      {rec.malScore && (
                        <div className="anime-meta">
                          <span className="mal-score">⭐ {rec.malScore}</span>
                          {rec.episodes && <span className="episodes">{rec.episodes} eps</span>}
                          {rec.year && <span className="year">{rec.year}</span>}
                        </div>
                      )}
                      {rec.genre && <p className="genre">{rec.genre}</p>}
                      {rec.description && (
                        <p className="description">
                          {rec.description.length > 150 
                            ? `${rec.description.substring(0, 150)}...` 
                            : rec.description}
                        </p>
                      )}
                      <div className="card-footer">
                        <a 
                          href={`https://myanimelist.net/anime/${rec.id}`} 
                          target="_blank" 
                          rel="noreferrer"
                        >
                          View on MAL →
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <button 
                className="reset-btn"
                onClick={() => {
                  setRecommendations([])
                  setSelectedAnime(null)
                  setQuery('')
                }}
              >
                Start Over
              </button>
            </>
          ) : null}
        </div>
      )}
    </div>
  )
}

export default App