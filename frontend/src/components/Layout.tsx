import { Link, useNavigate } from 'react-router-dom'
import { Outlet } from 'react-router-dom'

const Layout = () => {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-pink-50">
      {/* 헤더 */}
      <header className="bg-white shadow-md sticky top-0 z-50 border-b-2 border-orange-100">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link 
              to="/" 
              className="flex items-center gap-3 hover:opacity-80 transition-opacity"
            >
              <div className="p-2 bg-gradient-to-r from-orange-400 to-pink-500 rounded-full shadow-lg">
                <span className="text-3xl">🍳</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-orange-600 to-pink-600 bg-clip-text text-transparent">
                  레시피 추천 시스템
                </h1>
                <p className="text-xs text-gray-500">
                  보유한 재료로 레시피 찾기
                </p>
              </div>
            </Link>
            
            <nav className="flex items-center gap-4">
              <button
                onClick={() => navigate('/')}
                className="px-4 py-2 text-gray-700 hover:text-orange-600 hover:bg-orange-50 rounded-lg transition-colors font-medium"
              >
                🏠 홈
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* 메인 콘텐츠 */}
      <main className="container mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout


