interface SourcesListProps {
  sourceCount: number;
  isAssistantMessage: boolean;
}

export function SimpleSourcesList({ sourceCount, isAssistantMessage }: SourcesListProps) {
  return (
    <div className="mt-2 text-xs">
      <p className={isAssistantMessage ? "text-gray-500" : "text-indigo-200"}>
        {sourceCount > 0 
          ? `Response based on ${sourceCount} sources` 
          : "No sources used for this response"}
      </p>
    </div>
  );
}