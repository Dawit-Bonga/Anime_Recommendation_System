import { useState, useEffect } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

// Skeleton Loader Component
const SkeletonCard = () => (
  <div className="card skeleton-card">
    <div className="skeleton-image"></div>
    <div className="skeleton-content">
      <div className="skeleton-line skeleton-title"></div>
      <div className="skeleton-line skeleton-meta"></div>
      <div className="skeleton-line"></div>
      <div className="skeleton-line"></div>
      <div className="skeleton-line skeleton-short"></div>
    </div>
  </div>
)

// Empty State Component
const EmptyState = ({ message, icon = '🎌' }) => (
  <div className="empty-state">
    <div className="empty-icon">{icon}</div>
    <p className="empty-message">{message}</p>
  </div>
)

function App() {
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [selectedAnime, setSelectedAnime] = useState(null)
  const [myList, setMyList] = useState([])
  const [loading, setLoading] = useState(false)
  const [enriching, setEnriching] = useState(false)
  const [enrichingProgress, setEnrichingProgress] = useState({ current: 0, total: 0 })

  // Load My List from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('animeMyList')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed)) {
          setMyList(parsed)
        }
      } catch {
        // If parsing fails, clear the bad value
        localStorage.removeItem('animeMyList')
      }
    }
  }, [])

  // Persist My List to localStorage
  useEffect(() => {
    localStorage.setItem('animeMyList', JSON.stringify(myList))
  }, [myList])

  // 1. SEARCH FUNCTION
  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) {
      toast.error('Please enter an anime name to search')
      return
    }
    
    setLoading(true)
    try {
      const res = await axios.get(`${API_URL}/search?query=${encodeURIComponent(query.trim())}`)
      const results = res.data.results || []
      
      if (results.length === 0) {
        toast.error(`No results found for "${query}"`)
      } else {
        toast.success(`Found ${results.length} result${results.length > 1 ? 's' : ''}`)
      }
      
      setSearchResults(results)
      setRecommendations([]) // Clear old recommendations
      setSelectedAnime(null)
    } catch (error) {
      console.error("Error searching:", error)
      toast.error(error.response?.data?.detail || 'Failed to search. Please check if the server is running.')
    } finally {
      setLoading(false)
    }
  }

  // Keyboard navigation
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.key === 'Escape') {
        setQuery('')
        setSearchResults([])
        setRecommendations([])
        setSelectedAnime(null)
      }
    }
    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [])

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

  // Add anime to My List
  const addToMyList = (anime) => {
    if (myList.find(item => item.id === anime.id)) {
      toast.error('Already in your list')
      return
    }
    const updated = [...myList, anime]
    setMyList(updated)
    toast.success(`Added "${anime.title}" to your list`)
  }

  // Remove anime from My List
  const removeFromMyList = (animeId) => {
    const updated = myList.filter(item => item.id !== animeId)
    setMyList(updated)
    toast.success('Removed from your list')
  }

  // 3b. RECOMMENDATIONS BASED ON MY LIST (batch)
  const getListRecommendations = async () => {
    if (!myList.length) {
      toast.error('Add some anime to your list first')
      return
    }

    setLoading(true)
    toast.loading('Finding recommendations based on your list...', { id: 'list-recommendations' })

    try {
      const animeIds = myList.map(anime => anime.id)
      const res = await axios.post(
        `${API_URL}/recommend/batch`,
        animeIds,
        { params: { limit: 20 } }
      )

      const rawRecommendations = res.data.recommendations || []

      if (!rawRecommendations.length) {
        toast.error('No recommendations found', { id: 'list-recommendations' })
        setLoading(false)
        return
      }

      const inputTitles = res.data.input_titles || []

      setSelectedAnime({
        id: null,
        title: `Your List (${myList.length} anime${myList.length > 1 ? 's' : ''})`,
        isList: true,
        inputTitles,
      })
      setSearchResults([])

      toast.success(`Found ${rawRecommendations.length} recommendations!`, {
        id: 'list-recommendations',
      })

      // Enrich with images and descriptions from Jikan API
      setEnriching(true)
      setEnrichingProgress({ current: 0, total: rawRecommendations.length })
      const enrichedRecommendations = []

      for (let i = 0; i < rawRecommendations.length; i += 1) {
        const rec = rawRecommendations[i]
        const delay = i > 0 ? 350 : 0
        const details = await fetchAnimeDetails(rec.id, rec.title, delay)

        enrichedRecommendations.push({
          ...rec,
          image: details.image,
          description: details.description,
          malScore: details.score,
          episodes: details.episodes,
          year: details.year,
        })

        setEnrichingProgress({ current: i + 1, total: rawRecommendations.length })

        if (i === 0 || (i + 1) % 3 === 0) {
          setRecommendations([...enrichedRecommendations])
        }
      }

      setRecommendations(enrichedRecommendations)
      setEnriching(false)
      setEnrichingProgress({ current: 0, total: 0 })
    } catch (error) {
      console.error('Error getting list recommendations:', error)
      toast.error(error.response?.data?.detail || 'Failed to get recommendations', {
        id: 'list-recommendations',
      })
    } finally {
      setLoading(false)
    }
  }

  // 3. RECOMMEND FUNCTION
  const getRecommendations = async (animeId, animeTitle) => {
    setLoading(true)
    toast.loading('Finding recommendations...', { id: 'recommendations' })
    
    try {
      // 1. Get Recommendations from Python
      const res = await axios.get(`${API_URL}/recommend/${animeId}`)
      const rawRecommendations = res.data.recommendations || []
      
      if (rawRecommendations.length === 0) {
        toast.error('No recommendations found', { id: 'recommendations' })
        setLoading(false)
        return
      }
      
      // 2. Set the "Hero" anime (the one you clicked)
      setSelectedAnime({ id: animeId, title: animeTitle })
      setSearchResults([]) // Clear search results to show the recommendations
      
      toast.success(`Found ${rawRecommendations.length} recommendations!`, { id: 'recommendations' })
      
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
      
      if (error.response?.status === 404) {
        toast.error(`Sorry! The AI hasn't watched "${animeTitle}" yet (Not enough training data). Try a classic like Naruto or One Piece!`, { 
          id: 'recommendations',
          duration: 6000 
        })
      } else {
        toast.error(error.response?.data?.detail || 'Something went wrong connecting to the server.', { 
          id: 'recommendations' 
        })
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-container">
      {/* HEADER */}
      <header>
        <h1>🎌 Anime Recommender</h1>
        <p>Powered by Machine Learning (SVD)</p>
        <p className="keyboard-hint">Press <kbd>Esc</kbd> to clear • Press <kbd>Enter</kbd> to search</p>
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
              >
                <h4>{anime.title}</h4>
                <span className="id-badge">ID: {anime.id}</span>
                <div className="card-actions">
                  <button
                    type="button"
                    className="primary-btn"
                    onClick={() => getRecommendations(anime.id, anime.title)}
                  >
                    Get Recommendations
                  </button>
                  <button
                    type="button"
                    className="secondary-btn"
                    onClick={() => addToMyList(anime)}
                  >
                    + Add to My List
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* LOADING STATE WITH SKELETONS */}
      {loading && !searchResults.length && !recommendations.length && (
        <div className="results-section">
          <h3>Searching...</h3>
          <div className="grid">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="card skeleton-card">
                <div className="skeleton-line skeleton-title"></div>
                <div className="skeleton-line skeleton-short"></div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* EMPTY STATE - No search results */}
      {!loading && !searchResults.length && !recommendations.length && query && (
        <EmptyState 
          message="No results found. Try searching for a different anime!" 
          icon="🔍"
        />
      )}

      {/* MY LIST SECTION */}
      {myList.length > 0 && (
        <div className="my-list-section">
          <div className="my-list-header">
            <h3>My List ({myList.length})</h3>
            <button
              type="button"
              className="primary-btn"
              onClick={getListRecommendations}
              disabled={loading}
            >
              Get Recommendations for My List
            </button>
          </div>
          <div className="my-list-grid">
            {myList.map((anime) => (
              <div key={anime.id} className="my-list-item">
                <span className="my-list-title">{anime.title}</span>
                <button
                  type="button"
                  className="remove-btn"
                  onClick={() => removeFromMyList(anime.id)}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* RECOMMENDATIONS GRID */}
      {selectedAnime && (
        <div className="recommendations-section">
          {loading ? (
            <>
              <h2>Finding recommendations for <span>{selectedAnime.title}</span>...</h2>
              <div className="grid recommendations-grid">
                {[...Array(6)].map((_, i) => (
                  <SkeletonCard key={i} />
                ))}
              </div>
            </>
          ) : enriching ? (
            <>
              <h2>Loading details for <span>{selectedAnime.title}</span> recommendations...</h2>
              <div className="enriching-progress">
                <div className="progress-bar-container">
                  <div 
                    className="progress-bar"
                    style={{
                      width: `${(enrichingProgress.current / enrichingProgress.total) * 100}%`
                    }}
                  ></div>
                </div>
                <p className="progress-text">
                  Loading images and details... ({enrichingProgress.current}/{enrichingProgress.total})
                </p>
              </div>
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
                {[...Array(Math.max(0, 6 - recommendations.length))].map((_, i) => (
                  <SkeletonCard key={`skeleton-${i}`} />
                ))}
              </div>
            </>
          ) : recommendations.length > 0 ? (
            <>
              <h2>
                {selectedAnime.isList ? (
                  <>
                    Because you watched{' '}
                    <span>
                      {(selectedAnime.inputTitles || []).slice(0, 3).join(', ')}
                    </span>
                    {(selectedAnime.inputTitles || []).length > 3 && '...'}
                  </>
                ) : (
                  <>Because you liked <span>{selectedAnime.title}</span>:</>
                )}
              </h2>
              
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
                  toast.success('Cleared! Ready for a new search.')
                }}
              >
                Start Over
              </button>
            </>
          ) : (
            <EmptyState 
              message="No recommendations available. Try selecting a different anime!" 
              icon="📭"
            />
          )}
        </div>
      )}

      {/* INITIAL EMPTY STATE */}
      {!loading && !searchResults.length && !recommendations.length && !query && !selectedAnime && (
        <div className="welcome-section">
          <EmptyState 
            message="Search for an anime to get personalized recommendations powered by machine learning!" 
            icon="🎌"
          />
          <p className="welcome-hint">💡 Try searching for popular anime like "Naruto", "One Piece", or "Attack on Titan"</p>
        </div>
      )}
    </div>
  )
}

export default App