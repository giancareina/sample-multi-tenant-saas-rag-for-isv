// src/components/Footer.tsx

function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white border-t border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row justify-between items-center py-4 space-y-4 sm:space-y-0">
          <div className="flex items-center space-x-2 text-gray-500">
          </div>
          <div className="flex items-center space-x-6">
            <span className="text-sm text-gray-400">
              © {currentYear} ChatApp
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
