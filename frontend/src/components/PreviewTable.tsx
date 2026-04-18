import React, { useState } from 'react';

interface PreviewTableProps {
  data: any[];
}

const PAGE_SIZE = 100;

const PreviewTable: React.FC<PreviewTableProps> = ({ data }) => {
  const [currentPage, setCurrentPage] = useState(1);

  if (!data || data.length === 0) return null;

  const totalPages = Math.ceil(data.length / PAGE_SIZE);
  const startIndex = (currentPage - 1) * PAGE_SIZE;
  const endIndex = Math.min(startIndex + PAGE_SIZE, data.length);
  const paginatedData = data.slice(startIndex, endIndex);

  // Extract headers from the first object
  const headers = Object.keys(data[0]);

  const handlePrevPage = () => {
    setCurrentPage((prev) => Math.max(prev - 1, 1));
  };

  const handleNextPage = () => {
    setCurrentPage((prev) => Math.min(prev + 1, totalPages));
  };

  return (
    <div className="flex flex-col h-full w-full overflow-hidden">
      {/* Table Scroll Area */}
      <div className="flex-1 overflow-x-auto overflow-y-auto border border-gray-100 rounded-t-xl bg-white">
        <table className="divide-y divide-gray-200 text-sm table-auto w-auto">
          <thead className="bg-[#556B2F]/5 sticky top-0 z-10">
            <tr>
              {headers.map((header) => (
                <th
                  key={header}
                  className="px-3 py-3 text-left font-bold text-[#2F4F4F] uppercase tracking-wider whitespace-nowrap border-b border-r border-gray-100 last:border-r-0 bg-[#f9fafb]"
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-100">
            {paginatedData.map((row, rowIndex) => (
              <tr key={rowIndex} className="hover:bg-gray-50 transition-colors">
                {headers.map((header) => (
                  <td
                    key={`${rowIndex}-${header}`}
                    className="px-3 py-2 text-gray-700 max-w-[300px] truncate border-r border-gray-50 last:border-r-0"
                    title={row[header]?.toString() || ''}
                  >
                    {row[header]?.toString() || ''}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div className="bg-white border-x border-b border-gray-100 rounded-b-xl px-4 py-3 flex items-center justify-between text-sm text-gray-600 shadow-sm">
        <div>
          Показано <span className="font-medium">{startIndex + 1}</span> - <span className="font-medium">{endIndex}</span> з <span className="font-medium">{data.length}</span> записів
        </div>
        <div className="flex gap-2">
          <button
            onClick={handlePrevPage}
            disabled={currentPage === 1}
            className="px-3 py-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 disabled:opacity-40 disabled:hover:bg-transparent transition-all font-medium"
          >
            Назад
          </button>
          <div className="flex items-center px-2 font-medium">
            {currentPage} / {totalPages}
          </div>
          <button
            onClick={handleNextPage}
            disabled={currentPage === totalPages}
            className="px-3 py-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 disabled:opacity-40 disabled:hover:bg-transparent transition-all font-medium"
          >
            Вперед
          </button>
        </div>
      </div>
    </div>
  );
};

export default PreviewTable;
