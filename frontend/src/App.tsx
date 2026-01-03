import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import RecipeResultsPage from './pages/RecipeResultsPage'
import RecipeDetailPage from './pages/RecipeDetailPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="recipes" element={<RecipeResultsPage />} />
          <Route path="recipe" element={<RecipeDetailPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App

