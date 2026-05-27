import Sidebar from './Sidebar'

export default function Layout({ title, children }) {
  return (
    <div className="main-layout">
      <Sidebar />
      <div className="main-content">
        {title && (
          <header className="page-header">
            <h1 className="text-lg font-semibold text-gray-900">{title}</h1>
          </header>
        )}
        <main className="page-body">{children}</main>
      </div>
    </div>
  )
}
